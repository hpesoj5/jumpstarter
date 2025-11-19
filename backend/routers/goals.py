from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db import get_db
from backend import models, schemas

from typing import Union
import uuid
from google import genai
from datetime import date

import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

SYSTEM_INSTRUCTION = (
    "The current date today is: **{current_date_str}**\n"
    "You are an expert goal-setting and definition assistant.\n"
    "Your primary task is to guide your client through defining a high-quality goal using the SMART framework principles, ensuring all required fields are objective and present\n"
    "You may need to ask follow up questions that will help in planning for the goal.\n"

    "For a successful output ('DefinitionsCreate'), you MUST extract all three core fields: 'goal', 'metric', and 'purpose'.\n"
    "The 'goal' is what your client wants to achieve.\n"
    "The 'metric' is how they can determine if their 'goal' is achieved. This may have overlaps with 'goal' (i.e. 'land a job')\n" 
    "The 'purpose' is the reason they want to achieve their 'goal'. \n" 
    "The 'deadline' is when your client needs to achieve their 'goal'. **Format the deadline as YYYY-MM-DD**.\n\n"

    "**CRITICAL RULE FOR METRIC:** The 'metric' MUST be objective and quantifiable (e.g., 'score 85%', '20 pushups', 'finish $500 product'). "
    "Subjective metrics (e.g., 'performance ready', 'feel better', 'fluent') are NOT acceptable.\n\n"
    
    "**Conditional Output Rules:**\n"
    "1. **SUCCESS (Defined Deadline):** If all three core fields are present, high quality, AND the 'metric' is quantifiable, AND a clear deadline is given (e.g., 'by 2025-12-31'), use the 'DefinitionsCreate' schema.\n"
    "2. **SUCCESS (Estimated Deadline):** If all three core fields are present, high quality, AND the 'metric' is quantifiable, BUT no deadline or only a vague timeline is given (e.g., 'soon', '1 week later', 'Christmas'), use the 'DefinitionsCreate' schema. **Calculate and insert a reasonable deadline** based on the current date and the complexity of the goal.\n"
    "3. **FOLLOW-UP (Missing):** If the 'goal', 'metric', or 'purpose' is missing, use the 'FollowUp' schema, and ask for the missing data.\n"
    "4. **FOLLOW-UP (Subjective):** If the 'metric' is present but subjective, use the 'FollowUp' schema, and ask the user to make the metric objective and measurable. Suggest some metrics for the user to reference too.\n"
    
    "**FOLLOW-UP**: For 'question_to_user', ask **ONLY 1 question** to the user. You will be able to clarify information again after their response. If there are both missing fields and subjective metrics, ask for a missing field first."
)
client = genai.Client(api_key=GOOGLE_API_KEY)
chat_sessions = {}
ResponseSchema = Union[schemas.DefinitionsCreate, schemas.FollowUp]
router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/define", response_model=schemas.APIResponse)
def define_goal(goal_request: schemas.APIRequest, db: Session = Depends(get_db)):
    # Session exists; follow up questions
    if goal_request.session_id and goal_request.session_id in chat_sessions:
        session_id = goal_request.session_id
        chat = chat_sessions[session_id]
        
    else: # initial prompt
        session_id = str(uuid.uuid4())
        
        current_date_str = date.today().strftime('%Y-%m-%d')
        chat = client.chats.create(
            model='gemini-2.5-flash-lite',
            config={
                "system_instruction": SYSTEM_INSTRUCTION.format(current_date_str=current_date_str),
                "response_mime_type": "application/json",
                "response_schema": ResponseSchema,
            },
        )
        chat_sessions[session_id] = chat # Store the new session

    # gemini api call
    try:
        response = chat.send_message(goal_request.user_input)
        results = response.parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")

    if isinstance(results, schemas.DefinitionsCreate): # all required info extracted
        goal_data = results.model_dump()
        goal_data.pop('status')
        db_goal = models.Goal(**goal_data, owner_id=1)
        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        del chat_sessions[session_id]
        return schemas.APIResponse(session_id=session_id, data=results)
    
    elif isinstance(results, schemas.FollowUp): # follow up questions required
        return schemas.APIResponse(session_id=session_id, data=results)

    raise HTTPException(status_code=500, detail="LLM returned an unexpected format.")

# @router.get("/", response_model=list[schemas.Goal])
# def get_goals(db: Session = Depends(get_db)):
#     return db.query(models.Goal).all()