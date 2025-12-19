from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Goal
from utils import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/titles")
def get_stats(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    # returns list of all user goals
    goals = (
        db.query(Goal.id, Goal.title)
        .filter(Goal.owner_id == user_id)
        .all()
    )
    return [{"id": gid, "title": title} for gid, title in goals]
