from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, case
from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
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
    tasks_list = (
        db.query(models.Daily)
        .join(models.Daily.phase)
        .join(models.Phase.goal)
        .filter(
            models.Goal.owner_id == user_id,
            models.Daily.dailies_date <= current_date,
            models.Daily.is_completed == False,
            )
        .order_by(models.Daily.dailies_date)
        .all()
    )
    tasks_list = [schemas.DailyRead.model_validate(task, from_attributes=True) for task in tasks_list]
    completed_tasks_today = (
        db.query(
            func.sum(case((models.Daily.is_completed == True, 1), else_=0))
        )
        .join(models.Daily.phase)
        .join(models.Phase.goal)
        .filter(
            models.Goal.owner_id == user_id,
            models.Daily.completed_date == current_date,
        )
        .first()
    )
    remaining_tasks_today = len(tasks_list)
    completed_tasks_today = completed_tasks_today[0] if completed_tasks_today != None and completed_tasks_today[0] != None else 0
    return {
        "remaining_tasks_today": remaining_tasks_today,
        "completed_tasks_today": completed_tasks_today,
        "ongoing_goals": ongoing_goals,
        "completed_goals": completed_goals,
        "tasks_today_list": tasks_list,
    }

@router.post("/goal_progress", response_model=schemas.GoalProgressRead)
def get_goal_progress(request: schemas.TitleRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
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
        )
    )
    if request.goal_id != None:
        goals = goals.filter(models.Goal.id == request.goal_id)

    else:
        goals = goals.filter(models.Goal.is_completed == False)
        
    goals = goals.group_by(models.Goal.id).all()
    for goal in goals:
        if goal.completed_dailies == None:
            goal.completed_dailies = 0
    
    return { "goals": goals }

@router.post("/get_title")
def get_title(request: schemas.TitleRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    title = (
        db.query(models.Goal.title)
        .filter(
            models.Goal.id == request.goal_id,
            models.Goal.owner_id == user_id,
        )
        .first()
    )
    if title != None:
        title = title[0]
        
    return title

@router.post("/get_dailies", response_model = schemas.DailiesResponse)
def get_dailies(request: schemas.DailiesRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Gets all completed or uncompleted dailies with a specified goal id
    If DailiesRequest.completed == True, gets completed dailies, and vice versa
    """
    dailies_list = (
        db.query(models.Daily)
        .join(models.Daily.phase)
        .join(models.Phase.goal)
        .filter(
            models.Goal.owner_id == user_id,
            models.Goal.id == request.goal_id,
            models.Daily.is_completed == request.completed,
            )
        .order_by(models.Daily.dailies_date)
        .all()
    )
    dailies_list = schemas.DailiesResponse(
        dailies=[schemas.DailyRead.model_validate(task, from_attributes=True) for task in dailies_list]
    )
    
    return dailies_list

@router.patch("/mark_complete")
def mark_complete(update_req: schemas.UpdateRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Marks selected dailies as complete or incomplete. If UpdateRequest.completed == True, marks as complete and vice versa
    """
    current_date = date.today()
    try:
        dailies = (
            db.query(models.Goal, models.Daily)
            .join(models.Daily.phase)
            .join(models.Phase.goal)
            .filter(
                models.Daily.id.in_(update_req.ids),
                models.Goal.owner_id == user_id,
                models.Daily.is_completed == (not update_req.completed),
            )
            .all()
        )
        if not dailies:
            return {
                "message": "No dailies found",
                "updated": 0,
            }
        goals_to_check = set[models.Goal]()
        for goal, daily in dailies:
            daily.is_completed = update_req.completed
            daily.completed_date = current_date
            goals_to_check.add(goal)
            
        db.commit()
        print(f"Goals: {goals_to_check}")
        for goal in goals_to_check:
            uncompleted_goals = (
                db.query(models.Daily)
                .join(models.Daily.phase)
                .join(models.Phase.goal)
                .filter(
                    models.Goal.owner_id == user_id,
                    models.Goal.id == goal.id,
                    models.Daily.is_completed == False,
                )
                .count()
            )
            
            goal.is_completed = uncompleted_goals == 0
        
        db.commit()
        
        return {
            "message": "Dailies markead as completed",
            "updated": len(dailies),
        }
    
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the database."
        )
