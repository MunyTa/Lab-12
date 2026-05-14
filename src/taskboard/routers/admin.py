from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskboard.database import get_db
from taskboard.deps import get_current_admin
from taskboard.models import Card, User
from taskboard.schemas import UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserPublic])
def list_users(_: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.id).all()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete self")
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.commit()


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_card(
    card_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()
