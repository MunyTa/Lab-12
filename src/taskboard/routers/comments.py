from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskboard.database import get_db
from taskboard.deps import get_current_user
from taskboard.models import Board, Card, Comment, User
from taskboard.schemas import CommentCreate, CommentPublic

router = APIRouter(tags=["comments"])


def _ensure_card(db: Session, user: User, card_id: int) -> Card:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    lst = card.board_list
    board = db.get(Board, lst.board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.get("/cards/{card_id}/comments", response_model=list[CommentPublic])
def list_comments(
    card_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Comment]:
    _ensure_card(db, user, card_id)
    return db.query(Comment).filter(Comment.card_id == card_id).order_by(Comment.id).all()


@router.post("/cards/{card_id}/comments", response_model=CommentPublic, status_code=status.HTTP_201_CREATED)
def add_comment(
    card_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Comment:
    _ensure_card(db, user, card_id)
    comment = Comment(body=payload.body, card_id=card_id, user_id=user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    c = db.get(Comment, comment_id)
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")
    _ensure_card(db, user, c.card_id)
    if c.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(c)
    db.commit()
