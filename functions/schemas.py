from datetime import datetime
from pydantic import BaseModel, HttpUrl


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = None
    expires_at: datetime | None = None

class LinkUpdate(BaseModel):
    original_url: HttpUrl

class LinkStats(BaseModel):
    short_code: str
    original_url: str
    create_date: datetime
    clicks: int
    last_used_date: datetime | None