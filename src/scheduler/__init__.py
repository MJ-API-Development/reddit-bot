from pydantic import BaseModel
import praw
from src.config import config_instance

reddit_settings = config_instance().REDDIT_SETTINGS

class TaskScheduler:
    def __init__(self):
        self._reddit_api = praw.Reddit(
            client_id='YOUR_CLIENT_ID',
            client_secret='YOUR_CLIENT_SECRET',
            user_agent='YOUR_USER_AGENT',
            username='YOUR_REDDIT_USERNAME',
            password='YOUR_REDDIT_PASSWORD')

    async def run(self):
        pass
