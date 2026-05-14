from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from taskboard.database import get_db
from taskboard.deps import get_current_user
from taskboard.models import User
from taskboard.schemas import Token, UserCreate, UserPublic
from taskboard.security import authenticate_user, create_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.email == str(payload.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=str(payload.email), hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> User:
    return user
