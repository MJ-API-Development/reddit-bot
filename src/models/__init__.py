from typing import Optional

from pydantic import BaseModel, validator
from datetime import datetime


class RedditPost(BaseModel):
    title: str
    selftext: str
    submission_id: str | None
    created_utc_timestamp: int
    score: int | None
    url: str | None


class Submitted(BaseModel):
    id: str
    permalink: str


class RedditComment(BaseModel):
    body: str
    author: str
    created_utc: datetime
    score: int
    permalink: str



class Sentiment(BaseModel):
    article: str
    article_tldr: str
    link: str
    sentiment_article: None | str
    sentiment_title: None | str
    stock_codes: Optional[list[str]]

    @classmethod
    @validator('stock_codes')
    def stock_codes(cls, value: list[str] | None):
        if value is None:
            return []
        return value


class Resolution(BaseModel):
    url: str
    width: int
    height: int
    tag: str


class Thumbnail(BaseModel):
    resolutions: list[Resolution]


class ArticleData(BaseModel):
    datetime_published: str
    link: str
    providerPublishTime: int
    publisher: str
    sentiment: Sentiment
    thumbnail: Thumbnail
    tickers: list[str] | None
    title: str
    type: str
    uuid: str
