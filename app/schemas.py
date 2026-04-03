from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LinkCreate(BaseModel):
    target_url: HttpUrl


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    target_url: str
    click_count: int
    created_at: datetime


class LinkStats(BaseModel):
    short_code: str
    target_url: str
    click_count: int
    created_at: datetime
    recent_clicks: list[datetime]
