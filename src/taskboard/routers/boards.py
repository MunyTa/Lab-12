from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskboard.database import get_db
from taskboard.deps import get_current_user
from taskboard.models import Board, User
from taskboard.schemas import BoardCreate, BoardPublic, BoardUpdate

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("", response_model=list[BoardPublic])
def list_boards(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Board]:
    return db.query(Board).filter(Board.owner_id == user.id).order_by(Board.id).all()


@router.post("", response_model=BoardPublic, status_code=status.HTTP_201_CREATED)
def create_board(
    payload: BoardCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Board:
    board = Board(title=payload.title, description=payload.description, owner_id=user.id)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


@router.get("/{board_id}", response_model=BoardPublic)
def get_board(board_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Board:
    board = db.get(Board, board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.put("/{board_id}", response_model=BoardPublic)
def update_board(
    board_id: int,
    payload: BoardUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Board:
    board = db.get(Board, board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Board not found")
    if payload.title is not None:
        board.title = payload.title
    if payload.description is not None:
        board.description = payload.description
    db.commit()
    db.refresh(board)
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    board = db.get(Board, board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Board not found")
    db.delete(board)
    db.commit()
