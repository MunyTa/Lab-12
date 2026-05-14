from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taskboard.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    boards: Mapped[list[Board]] = relationship(
        "Board", back_populates="owner", cascade="all, delete-orphan"
    )
    comments: Mapped[list[Comment]] = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    owner: Mapped[User] = relationship("User", back_populates="boards")
    lists: Mapped[list[BoardList]] = relationship(
        "BoardList",
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardList.position",
    )


class BoardList(Base):
    """Колонка доски (как список в Trello)."""

    __tablename__ = "board_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), nullable=False, index=True)

    board: Mapped[Board] = relationship("Board", back_populates="lists")
    cards: Mapped[list[Card]] = relationship(
        "Card", back_populates="board_list", cascade="all, delete-orphan", order_by="Card.position"
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    list_id: Mapped[int] = mapped_column(ForeignKey("board_lists.id"), nullable=False, index=True)

    board_list: Mapped[BoardList] = relationship("BoardList", back_populates="cards")
    comments: Mapped[list[Comment]] = relationship(
        "Comment", back_populates="card", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    card: Mapped[Card] = relationship("Card", back_populates="comments")
    author: Mapped[User] = relationship("User", back_populates="comments")
