from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from taskboard.database import get_db
from taskboard.deps import get_current_user
from taskboard.models import Board, BoardList, Card, Comment, User
from taskboard.routers.cards import count_overdue_for_board
from taskboard.schemas import BoardAnalytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/boards/{board_id}", response_model=BoardAnalytics)
def board_summary(
    board_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardAnalytics:
    board = db.get(Board, board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Board not found")

    lists_count = db.query(func.count(BoardList.id)).filter(BoardList.board_id == board_id).scalar() or 0
    total_cards = (
        db.query(func.count(Card.id)).join(BoardList).filter(BoardList.board_id == board_id).scalar() or 0
    )
    total_comments = (
        db.query(func.count(Comment.id))
        .join(Card)
        .join(BoardList)
        .filter(BoardList.board_id == board_id)
        .scalar()
        or 0
    )
    overdue = count_overdue_for_board(db, board_id)
    return BoardAnalytics(
        board_id=board_id,
        total_cards=int(total_cards),
        overdue_cards=int(overdue),
        total_comments=int(total_comments),
        lists_count=int(lists_count),
    )
