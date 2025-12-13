from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
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
            func.sum(case((models.Goal.is_completed == False, 1)), else_=0).label("ongoing"),
            func.sum(case((models.Goal.is_completed == True, 1)), else_=0).label("completed"),
        )
        .filter(models.Goal.owner_id == user_id)
        .first()
    )
    ongoing_goals = goals.ongoing if goals.ongoing != None else 0
    completed_goals = goals.completed if goals.completed != None else 0
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
    remaining_tasks_today = tasks.ongoing if tasks.ongoing != None else 0
    completed_tasks_today = tasks.completed if tasks.completed != None else 0
    return {
        "remaining_tasks_today": remaining_tasks_today,
        "completed_tasks_today": completed_tasks_today,
        "ongoing_goals": ongoing_goals,
        "completed_goals": completed_goals,
        "tasks_today_list": tasks_today_list,
    }

@router.get("/goal_progress", response_model=schemas.GoalProgressRead)
def get_goal_progress(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns stats for the dashboard goal progress card
    """
    goals = (
        db.query(
            models.Goal.title,
            models.Goal.deadline,
            func.count(models.Daily.id).label("total_dailies"),
            func.sum(case((models.Daily.is_completed == True, 1), else_=0)).label("completed_dailies")
        )
        .join(models.Daily.phase)
        .join(models.Phase.goal)
        .filter(
            models.Goal.owner_id == user_id,
            models.Goal.is_completed == False,
        )
        .group_by(models.Goal.id)
        .all()
    )
    for goal in goals:
        if goal.completed_dailies == None:
            goal.completed_dailies = 0
    
    return { "goals": goals }

@router.patch("/mark_complete")
def mark_complete(selected_ids = schemas.DailyIdsList, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Marks selected dailies as complete
    """
    try:
        dailies = (
            db.query(models.Daily)
            .join(models.Daily.phase)
            .join(models.Phase.goal)
            .filter(
                models.Daily.id.in_(selected_ids.ids),
                models.Goal.owner_id == user_id,
                models.Goal.is_completed == False,
            )
            .all()
        )
        
        if not dailies:
            return {
                "message": "No dailies found",
                "updated": 0,
            }
        
        for daily in dailies:
            daily.is_completed = True
            
        db.commit()
        
        return {
            "message": "Dailies markead as completed",
            "updated": len(dailies),
        }
    
    except SQLAlchemyError as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the database."
        )
