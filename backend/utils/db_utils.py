from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import select, delete, update

from google import genai
from google.genai import types
from typing import List, Union

from backend import schemas, models
from models import (
    User,
    Goal,
    ChatHistory, ChatSession
)
from schemas import (
    FollowUp, DefinitionsCreate, PhaseGeneration,
)

APIResponse = Union[FollowUp, DefinitionsCreate, PhaseGeneration]
def get_user_session_details(db: Session, user_id: int):
    result = db.query(
        ChatSession.session_id,
        ChatSession.current_phase,
        ChatSession.goal_id
    ).select_from(User).join(
        ChatSession, User.current_session == ChatSession.session_id
    ).filter(
        User.id == user_id
    ).first()

    return result

def get_chat_history(session_id, db):
    results = db.query(ChatHistory)\
            .filter(ChatHistory.session_id == session_id)\
            .order_by(ChatHistory.text_num)\
            .all()
    history = []
    for role, content_text in results:
        history.append(
            types.Content(
                role=role, 
                parts=[types.Part.from_text(content_text)]
            )
        )
    return history

def get_last_message(db: Session, session_id: int):
    last_message_model = db.query(ChatHistory)\
        .filter(ChatHistory.session_id == session_id)\
        .order_by(ChatHistory.text_num.desc())\
        .first()
        
    if last_message_model:
        return last_message_model.content
    return None

def add_message_to_history(db: Session, session_id: int, role: str, content: str):
    """Adds a new message to the chat history."""
    max_text_num = db.query(func.max(ChatHistory.text_num))\
        .filter(ChatHistory.session_id == session_id)\
        .scalar()
        
    next_text_num = (max_text_num or 0) + 1
    
    new_message = ChatHistory(
        session_id=session_id,
        text_num=next_text_num,
        role=role,
        content=content
    )
    
    db.add(new_message)

def clear_chat_history(db: Session, session_id: int):
    db.query(ChatHistory)\
    .filter(ChatHistory.session_id == session_id)\
    .delete(synchronize_session='fetch')

def reset_session(db: Session, user_id: int):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"User with id {user_id} not found.")
            return False
            
        if not user.current_session:
            print(f"User {user_id} has no current session.")
            return False

        session = db.query(ChatSession).filter(
            ChatSession.session_id == user.current_session
        ).first()

        if not session:
            print(f"Session with id {user.current_session} not found (data integrity issue).")
            return False

        if session.goal_id:
            goal = db.query(Goal).filter(Goal.id == session.goal_id).first()
            if goal:
                db.delete(goal)

        
        session.current_phase = 1
        session.goal_id = None
        session.history = []
        db.add(session)
        return True

    except Exception as e:
        db.rollback()
        return False