from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.db import get_db
from backend import models, schemas
from backend.utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session=Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(new_user)
    db.flush()
    db.commit()
    db.refresh(new_user)
    token = create_access_token({"uid": new_user.id, "username": user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
def login(user: schemas.UserLogin, db: Session=Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token({"uid": db_user.id, "username": db_user.username})
    return {"access_token": token, "token_type": "bearer"}
