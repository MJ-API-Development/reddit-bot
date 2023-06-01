import datetime
import asyncio
from asyncio import Queue

from praw.models import SubredditHelper, Submission
import requests
from pydantic import BaseSettings, ValidationError
import praw
from src.config import config_instance, RedditSettings
from src.logger import init_logger
from src.models import RedditPost, ArticleData

FIVE_MINUTE = 300


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
            user_agent=reddit_settings.user_agent,
            username=reddit_settings.username,
            password=reddit_settings.password)
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
            subreddit = self._reddit_api.subreddit(self._subreddit_name)
            submission: Submission = subreddit.submit(title=post.title, selftext=post.selftext, url=post.url)
            post.submission_id = submission.id
            _submission = post, submission
            self.reddit_submissions.append(_submission)
            return True
        except Exception as e:
            self._logger.error(f"Error submitting reddit post: {str(e)}")
        return False

    async def create_article_post(self, article: ArticleData) -> RedditPost | None:
        """
            **compile_article_post**
                takes in financial article and create a reddit post
        :param article:
        :return:
        """
        _post = dict(title=article.title, selftext=article.sentiment.article_tldr,
                     created_utc_timestamp=create_utc_timestamp())
        try:
            reddit_post: RedditPost = RedditPost(**_post)
            self._logger.info(f'created Reddit Post : {reddit_post}')
            return reddit_post

        except ValidationError as e:
            self._logger.error(f"Error occured creating reddit post")

        return None

    async def create_posts(self):
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


def create_utc_timestamp() -> int:
    return int(datetime.datetime.utcnow().timestamp())
