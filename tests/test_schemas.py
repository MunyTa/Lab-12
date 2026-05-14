import pytest
from pydantic import ValidationError

from taskboard.schemas import BoardCreate, CardCreate, UserCreate


def test_user_password_too_short() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="x@y.com", password="short")


def test_board_title_empty() -> None:
    with pytest.raises(ValidationError):
        BoardCreate(title="")


def test_board_title_stripped() -> None:
    b = BoardCreate(title="  Sprint  ")
    assert b.title == "Sprint"


def test_card_title_ok() -> None:
    c = CardCreate(title="OK")
    assert c.title == "OK"
