from pydantic import BaseSettings, Field


class Logging(BaseSettings):
    filename: str = Field(default="reddit.log")


class APPSettings(BaseSettings):
    """APP Confi settings"""
    APP_NAME: str = Field(default="ESA-Reddit-Bot")
    TITLE: str = Field(default="EOD-Stock-API - Financial Data Reddit Bot")
    DESCRIPTION: str = Field(
        default="Reddit-Bot to send EOD-Stock-API Financial Data to Reddit for Promotional Purposes")
    VERSION: str = Field(default="1.0.0")
    TERMS: str = Field(default="https://eod-stock-api.site/terms")
    CONTACT_NAME: str = Field(default="MJ API Development")
    CONTACT_URL: str = Field(default="https://eod-stock-api.site/contact")
    CONTACT_EMAIL: str = Field(default="info@eod-stock-api.site")
    LICENSE_NAME: str = Field(default="Apache 2.0")
    LICENSE_URL: str = Field(default="https://www.apache.org/licenses/LICENSE-2.0.html")
    DOCS_URL: str = Field(default='/docs')
    OPENAPI_URL: str = Field(default='/openapi')
    REDOC_URL: str = Field(default='/redoc')


class RedditSettings(BaseSettings):
    client_id: str = Field(..., env='REDDIT_CLIENT_ID')
    client_secret: str = Field(..., env='REDDIT_CLIENT_SECRET')
    user_agent: str = Field(..., env='REDDIT_USER_AGENT')
    username: str = Field(..., env='REDDIT_USERNAME')
    password: str = Field(..., env='REDDIT_PASSWORD')
    subreddit_name: str = Field(..., env='SUB_REDDIT')

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


class Settings(BaseSettings):
    EOD_API_KEY: str = Field(..., env='EOD_STOCK_API_KEY')
    DEVELOPMENT_SERVER_NAME: str = Field(..., env='DEVELOPMENT_SERVER_NAME')
    APP_SETTINGS: APPSettings = APPSettings()
    REDDIT_SETTINGS: RedditSettings = RedditSettings()
    LOGGING: Logging = Logging()

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


def config_instance() -> Settings:
    return Settings()
