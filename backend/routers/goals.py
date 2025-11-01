from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend import models, schemas

router = APIRouter(prefix="/goals", tags=["Goals"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.goal.Goal)
def create_goal(goal: schemas.goal.GoalCreate, db: Session = Depends(get_db)):
    new_goal = models.goal.Goal(**goal.model_dump(), owner_id=1)  # temporary user
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal

@router.get("/", response_model=list[schemas.goal.Goal])
def get_goals(db: Session = Depends(get_db)):
    return db.query(models.goal.Goal).all()
