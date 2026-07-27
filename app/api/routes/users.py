from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.schema.users import UserCreate, UserUpdate, UserResponse, Token
from app.crud import users as users_crud
from app.api.depandance import get_current_user
from app.models.users import User

router = APIRouter()

# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username + password, receive a JWT access token."""
    user = users_crud.get_user_by_login(db, login=form.username)
    if not user or not verify_password(form.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}

# ── CRUD (protected) ──────────────────────────────────────────────────────────

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    # _: User = Depends(get_current_user),   # must be logged in
):
    if users_crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return users_crud.create_user(db=db, user=user)

@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    # _: User = Depends(get_current_user),
):
    return users_crud.get_users(db, skip=skip, limit=limit)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently logged-in user."""
    return current_user

@router.get("/admin-phone")
def get_admin_phone(db: Session = Depends(get_db)):
    """Return the admin phone number."""
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        return {"phone": "+213000000000"} # fallback
    return {"phone": admin.phone}

@router.get("/{id}", response_model=UserResponse)
def get_user(
    id: int,
    db: Session = Depends(get_db),
    # _: User = Depends(get_current_user),
):
    user = users_crud.get_user(db, user_id=id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{id}", response_model=UserResponse)
def update_user(
    id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    # _: User = Depends(get_current_user),
):
    updated = users_crud.update_user(db, user_id=id, user=user)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    deleted = users_crud.delete_user(db, user_id=id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="User not found")
