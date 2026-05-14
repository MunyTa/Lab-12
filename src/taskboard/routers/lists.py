from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskboard.database import get_db
from taskboard.deps import get_current_user
from taskboard.models import Board, BoardList, User
from taskboard.schemas import BoardListCreate, BoardListPublic

router = APIRouter(tags=["lists"])


def _board_owned(db: Session, user: User, board_id: int) -> Board:
    board = db.get(Board, board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.get("/boards/{board_id}/lists", response_model=list[BoardListPublic])
def list_lists(
    board_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[BoardList]:
    _board_owned(db, user, board_id)
    return (
        db.query(BoardList)
        .filter(BoardList.board_id == board_id)
        .order_by(BoardList.position, BoardList.id)
        .all()
    )


@router.post("/boards/{board_id}/lists", response_model=BoardListPublic, status_code=status.HTTP_201_CREATED)
def create_list(
    board_id: int,
    payload: BoardListCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardList:
    _board_owned(db, user, board_id)
    lst = BoardList(title=payload.title, position=payload.position, board_id=board_id)
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return lst


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    lst = db.get(BoardList, list_id)
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    _board_owned(db, user, lst.board_id)
    db.delete(lst)
    db.commit()
