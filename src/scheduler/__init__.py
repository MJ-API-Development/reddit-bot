import datetime

from praw.models import SubredditHelper, Submission
import requests
from pydantic import BaseSettings, ValidationError
import praw
from src.config import config_instance, RedditSettings
from src.logger import init_logger
from src.models import RedditPost, ArticleData


class TaskScheduler:
    def __init__(self, reddit_settings: RedditSettings = config_instance().REDDIT_SETTINGS):
        self._article_count: int = 50
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

    async def create_post(self, post: RedditPost) -> tuple[RedditPost, Submission]:
        """
            **create_post**
                creates post and returns Post and Submission Models
        :param post:
        :return:
        """
        subreddit = self._reddit_api.subreddit(self._subreddit_name)
        submission: Submission = subreddit.submit(title=post.title, selftext=post.selftext, url=post.url)
        post.submission_id = submission.id
        return post, submission

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


    async def run(self):
        pass


def create_utc_timestamp() -> int:
    return int(datetime.datetime.utcnow().timestamp())