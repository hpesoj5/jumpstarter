from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db import get_db
from backend import models, schemas

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/", response_model=schemas.Goal)
def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db)):
    new_goal = models.Goal(**goal.model_dump(), owner_id=1)  # temporary user
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal

@router.get("/", response_model=list[schemas.Goal])
def get_goals(db: Session = Depends(get_db)):
    return db.query(models.Goal).all()
