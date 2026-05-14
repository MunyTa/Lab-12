from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskboard.database import get_db
from taskboard.deps import get_current_user
from taskboard.models import Board, BoardList, Card, User
from taskboard.schemas import CardCreate, CardPublic, CardUpdate

router = APIRouter(tags=["cards"])


def _ensure_list(db: Session, user: User, list_id: int) -> BoardList:
    lst = db.get(BoardList, list_id)
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    board = db.get(Board, lst.board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="List not found")
    return lst


@router.get("/lists/{list_id}/cards", response_model=list[CardPublic])
def list_cards(
    list_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Card]:
    _ensure_list(db, user, list_id)
    return db.query(Card).filter(Card.list_id == list_id).order_by(Card.position, Card.id).all()


@router.post("/lists/{list_id}/cards", response_model=CardPublic, status_code=status.HTTP_201_CREATED)
def create_card(
    list_id: int,
    payload: CardCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Card:
    _ensure_list(db, user, list_id)
    card = Card(
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        position=payload.position,
        list_id=list_id,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.put("/cards/{card_id}", response_model=CardPublic)
def update_card(
    card_id: int,
    payload: CardUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Card:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    _ensure_list(db, user, card.list_id)
    data = payload.model_dump(exclude_unset=True)
    new_list_id = data.pop("list_id", None)
    if new_list_id is not None:
        _ensure_list(db, user, new_list_id)
        card.list_id = new_list_id
    for field, value in data.items():
        setattr(card, field, value)
    db.commit()
    db.refresh(card)
    return card


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    _ensure_list(db, user, card.list_id)
    db.delete(card)
    db.commit()


def count_overdue_for_board(db: Session, board_id: int) -> int:
    now = datetime.now(timezone.utc)
    return (
        db.query(Card)
        .join(BoardList, Card.list_id == BoardList.id)
        .filter(BoardList.board_id == board_id, Card.due_date.isnot(None), Card.due_date < now)
        .count()
    )
