from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_admin: bool


class BoardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)


class BoardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class BoardPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    owner_id: int


class BoardListCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    position: int = 0


class BoardListPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    position: int
    board_id: int


class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    due_date: datetime | None = None
    position: int = 0


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    due_date: datetime | None = None
    position: int | None = None
    list_id: int | None = None


class CardPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    due_date: datetime | None
    position: int
    list_id: int


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    created_at: datetime
    card_id: int
    user_id: int


class BoardAnalytics(BaseModel):
    board_id: int
    total_cards: int
    overdue_cards: int
    total_comments: int
    lists_count: int
