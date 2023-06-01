import asyncio
import datetime
from asyncio import Queue

import praw
import requests
from praw.models import Submission
from pydantic import ValidationError

from src.config import config_instance, RedditSettings
from src.logger import init_logger
from src.models import RedditPost

FIVE_MINUTE = 300


def create_utc_timestamp() -> int:
    return int(datetime.datetime.utcnow().timestamp())


def compose_default_reds(title: str, post_lines: list[str], url: str | None = None):
    post_content = "\n".join(post_lines)
    time_stamp = create_utc_timestamp()
    reddit_post = dict(title=title, created_utc_timestamp=time_stamp)
    if url:
        reddit_post.update(dict(media_link=url))
    else:
        reddit_post.update(dict(selftext=post_content))

    return RedditPost(**reddit_post)


DEFAULT_POSTS = [
    compose_default_reds(title="EOD Stock Market API", post_lines=[
        "- Exchange & Ticker Data",
        "- (EOD) Stock Data",
        "- Fundamental Data",
        "- Stock Options And Splits Data",
        "- Financial News API",
        "- Social Media Trend Data For Stocks",
        "Create A free API Key today",
        "https://eod-stock-api.site/plan-descriptions/basic"
    ]),

    compose_default_reds(title="Financial & Business News API", post_lines=[
        "- Articles By UUID",
        "- Articles By Publishing Date",
        "- Articles By Stock Tickers",
        "- Articles By Exchange",
        "- Get List of Exchanges & Tickers",
        "- Get List of Publishers & Articles By Publisher",
        "Create A free API Key today",
        "https://bit.ly/financial-business-news-api"
    ])
]


def create_user_agent(client_id: str) -> str:
    return f"Python:{client_id}:1.0 (by /u/mobius-crypt)"


class TaskScheduler:
    def __init__(self, reddit_settings: RedditSettings = config_instance().REDDIT_SETTINGS):
        self._article_count: int = 50
        self._error_delay: int = FIVE_MINUTE
        self._article_queue: Queue = Queue()
        self._reddit_posts_queue: Queue = Queue()
        self.reddit_submissions: list[tuple[RedditPost, Submission]] = []
        self._reddit_api = praw.Reddit(
            client_id=reddit_settings.client_id,
            client_secret=reddit_settings.client_secret,
            username=reddit_settings.username,
            password=reddit_settings.password,
            user_agent=create_user_agent(reddit_settings.client_id)
        )
        self._access_token: str | None = None
        self._subreddit_name = reddit_settings.subreddit_name
        self._logger = init_logger(self.__class__.__name__)

    async def fetch_articles(self):
        self._logger.info("Fetching Articles from API")
        _params: dict[str, str] = {'api_key': config_instance().EOD_API_KEY}
        articles_url: str = f"https://gateway.eod-stock-api.site/api/v1/news/articles-bounded/{self._article_count}"
        try:
            with requests.Session() as session:
                response = session.get(url=articles_url, params=_params)
                response.raise_for_status()
                if response.headers.get('Content-Type') == 'application/json':
                    return response.json()
                return None

        except Exception as e:
            self._logger.error(f"Error fetching articles : {str(e)}")
            return None

    async def submit_article_post(self, post: RedditPost) -> bool:
        """
            **create_post**
                creates post and returns Post and Submission Models
        :param post:
        :return:
        """
        try:
            # submission = make_post(access_token=self._access_token, subreddit=self._subreddit_name,
            #                        title=post.title, content=post.selftext)
            subreddit = self._reddit_api.subreddit(self._subreddit_name)
            if post.media_link:
                submission: Submission = subreddit.submit(title=post.title, url=post.media_link)
                submission.reply(body=post.selftext)
            else:
                submission = subreddit.submit(title=post.title, selftext=post.selftext)

            self._logger.info(f"submission : {submission}")

            return True
        except Exception as e:
            self._logger.error(f"Error submitting reddit post: {str(e)}")
        return False

    async def create_article_post(self, article: dict[str, str]) -> RedditPost | None:
        """
            **compile_article_post**
                takes in financial article and create a reddit post
        :param article:
        :return:
        """
        self_text = article.get('sentiment', {}).get('article_tldr') or article.get('sentiment', {}).get('article')
        if not self_text:
            self_text = article.get('title')
        self_text = f"{self_text}/n {article.get('link')}"
        image_resolutions: list[dict[str, str | int]] = article.get('thumbnail', {}).get('resolutions')
        _post = dict()
        if image_resolutions:
            _resolution: dict[str, str | int] = image_resolutions[0]
            _post.update(dict(media_link=_resolution.get('url')))

        _post.update(title=article.get('title'), selftext=self_text, created_utc_timestamp=create_utc_timestamp())

        try:
            reddit_post: RedditPost = RedditPost(**_post)
            self._logger.info(f'created Reddit Post : {reddit_post}')
            return reddit_post

        except ValidationError as e:
            self._logger.error(f"Error occurred creating reddit post : {str(e)}")

        return None

    async def create_posts(self):

        for reddit_post in DEFAULT_POSTS:
            await self._reddit_posts_queue.put(reddit_post)

        while self._article_queue.qsize() > 0:
            self._logger.info(f"Articles Remaining : {self._article_queue.qsize()}")
            article = await self._article_queue.get()
            if article:
                try:
                    reddit_post: RedditPost = await self.create_article_post(article=article)
                    self._logger.info(f"Created reddit post: {reddit_post}")
                    await self._reddit_posts_queue.put(item=reddit_post)
                except ValidationError as e:
                    self._logger.error(f"Validation Error Creating Reddit Post : {str(e)}")

    async def run(self):
        self._logger.info("Started Run")
        # session, access_token = await authenticate_reddit()
        # self._access_token = access_token
        if self._reddit_posts_queue.qsize() == 0:
            response: dict[str, str | dict[str, str] | int] = await self.fetch_articles()
            if response.get('status'):
                payload = response.get('payload', [])
                for article in payload:
                    self._logger.info(f"Article : {article}")
                    await self._article_queue.put(item=article)

            # will use the articles on articles queue to create reddit posts
            await self.create_posts()

            reddit_post: RedditPost = await self._reddit_posts_queue.get()
            if reddit_post:
                reddit_post_sent = await self.submit_article_post(post=reddit_post)
                while not reddit_post_sent:
                    await asyncio.sleep(delay=self._error_delay)
                    reddit_post: RedditPost = await self._reddit_posts_queue.get()
                    reddit_post_sent = await self.submit_article_post(post=reddit_post)
