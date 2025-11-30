from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from backend.db import get_db
from backend import models, schemas
from backend.utils import get_current_user
from datetime import date

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_stats(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns stats of top row cards (
        remaining tasks today,
        completed tasks today,
        goals in progress (ongoing goals),
        completed goals,
    ) and the tasks for the day.
    """
    current_date = date.today()
    goals = (
        db.query(
            func.sum(case((models.Goal.is_completed == False, 1), else_=0)).label("ongoing"),
            func.sum(case((models.Goal.is_completed == True, 1), else_=0)).label("completed"),
        )
        .filter(models.Goal.owner_id == user_id)
        .first()
    )
    ongoing_goals = goals.ongoing
    completed_goals = goals.completed
    tasks_today_list = (
        db.query(models.Daily)
        .join(models.Daily.phase)
        .join(models.Phase.goal)
        .filter(
            models.Goal.owner_id == user_id,
            models.Daily.dailies_date == current_date,
            models.Daily.is_completed == False,
            )
        .all()
    )
    tasks_today_list = [schemas.DailyRead.model_validate(task, from_attributes=True) for task in tasks_today_list]
    tasks = (
        db.query(
            func.sum(case((models.Daily.is_completed == False, 1), else_=0)).label("ongoing"),
            func.sum(case((models.Daily.is_completed == True, 1), else_=0)).label("completed"),
        )
        .join(models.Daily.phase)
        .join(models.Phase.goal)
        .filter(
            models.Goal.owner_id == user_id,
            models.Daily.dailies_date == current_date,
        )
        .first()
    )
    remaining_tasks_today = tasks.ongoing
    completed_tasks_today = tasks.completed
    return {
        "remaining_tasks_today": remaining_tasks_today,
        "completed_tasks_today": completed_tasks_today,
        "ongoing_goals": ongoing_goals,
        "completed_goals": completed_goals,
        "tasks_today_list": tasks_today_list,
    }
