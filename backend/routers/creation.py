import datetime, pickle, json
from datetime import date
from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, TypeAdapter, Field
from sqlalchemy.orm import Session, joinedload

from backend.utils import hash_password
from backend.db import get_db

from backend.models import User, ChatSession, Goal, Phase, Daily
from backend.schemas import (FollowUp, DefinitionsCreate, 
                            CurrentState, FixedResources, Constraints, GoalPrerequisites, 
                            PhaseGeneration, PhaseCreate)
from backend.utils.system_instruction import SYSTEM_INSTRUCTION

from google import genai
from google.genai.types import Content, Part

import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

APIResponse = Union[FollowUp , DefinitionsCreate , GoalPrerequisites , PhaseGeneration]

class APIRequest(BaseModel):
    user_id: int | None = None
    user_input: str

class confirmRequest(BaseModel):
    user_id: int | None = None
    confirm_obj: DefinitionsCreate | PhaseGeneration

client = genai.Client(api_key=GOOGLE_API_KEY)
router = APIRouter(prefix="/create", tags=["Goals"])

@router.post("/load", response_model=APIResponse)
def load(request: APIRequest, db: Session = Depends(get_db)):
    if request.user_id == None:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        last_response = get_model_latest_response(request.user_id, db)
        if last_response == None:
            return FollowUp('follow_up_required', "What would you like to achieve today?")
        return last_response

@router.post("/query", response_model=APIResponse)
def query(request: APIRequest, db: Session = Depends(get_db)):
    if request.user_id == None:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        user_db_session = get_user_session(request.user_id, db)
        response_raw = get_llm_response(user_db_session, request.user_input, db)
        response_parsed = parse_response(response_raw)
        if isinstance(response_parsed, GoalPrerequisites):
            update_session_prereq(user_db_session, response_parsed)
        update_session_chat_history(user_db_session, request.user_input, response_raw, db)
        db.commit()
        return response_parsed
    
@router.post("/confirm", response_model=APIResponse)
def confirm(request: confirmRequest, db: Session = Depends(get_db)):
    if request.user_id == None:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        user_db_session = get_user_session(request.user_id, db)
        if isinstance(request.confirm_obj, DefinitionsCreate):
            update_session_goal(user_db_session, request.confirm_obj, db)
            transition = APIRequest(user_id=request.user_id, user_input=f'My goal is {request.confirm_obj.model_dump_json()}\nWhat prerequisites do you need from me?')
            return query(transition, db)
        elif isinstance(request.confirm_obj, PhaseGeneration):
            print("here")
            #finialise_session()

def insert_session(db: Session=Depends(get_db)): # will not commit in this function. commits should happen with what calls it.
    try:
        new_session = ChatSession(session_data=pickle.dumps([]))
        db.add(new_session)
        db.flush()
        db.refresh(new_session)
        print(f"new session with id: {new_session.id} added")
        return new_session
    except Exception as e:
        print("error with new session: ", e)
        return False
    
def insert_user(username, email, password, db: Session=Depends(get_db)):
    # insert new user into db
    try:
        new_session = insert_session(db)
        new_user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            session=new_session
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User new user with uid: {new_user.id} added")
        return new_user.id
    except Exception as e:
        print("error with new user: ", e)
        return False

def change_user_session(uid, db: Session=Depends(get_db)):
    # creates new session and updates user to a new session
    try:
        user = db.get(User, uid)
        new_session = insert_session(db)
        user.session = new_session
        db.commit()
        db.refresh()
        print(f"User {user.username} (uid: {uid}), successfully updated session")
        return new_session

    except Exception as e:
        print(e)
        return False
    
def get_user_session(uid, db: Session=Depends(get_db)) -> ChatSession: 
    try:
        user = db.query(User).options(
            joinedload(User.session)
        ).filter(User.id == uid).first()
        
        if not user:
            raise HTTPException(status_code=500, detail=f"User with ID {uid} not found.")
        
        if not user.session:
            print(f"User {uid} does not have an active session.")
            return change_user_session(uid, db)
        print("user session found: ", user.session)
        return user.session
    
    except Exception as e:
        print("unable to get user session: ", e)
        return False

def get_model_latest_response(uid, db: Session=Depends(get_db)):
    models = TypeAdapter(FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration)
    session = get_user_session(uid, db)
    chat_history = pickle.loads(session.session_data)
    text_obj = json.loads(chat_history[-1].parts[0].text)
    return models.validate_python(text_obj)

def update_session_data(session: ChatSession, session_data, db: Session=Depends(get_db)):
    try:
        session.session_data = pickle.dumps(session_data)
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    except Exception as e:
        print("Error with updating session data: ", e)
        return False
    
def update_session_goal(session: ChatSession, goal, db: Session=Depends(get_db)):
    try:
        if isinstance(goal, DefinitionsCreate):
            goal = goal.model_dump_json()
        session.goal_obj = goal
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    except Exception as e:
        print("Error with updating session goal_obj: ", e)
        return False
    
def update_session_prereq(session: ChatSession, prereq, db: Session=Depends(get_db)):
    try:
        if isinstance(prereq, GoalPrerequisites):
            prereq = prereq.model_dump_json()
        session.prereq_obj = prereq
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    except Exception as e:
        print("Error with updating session prereq_obj: ", e)
        return False
    
def update_session_phases(session: ChatSession, phases, db: Session=Depends(get_db)):
    try:
        if isinstance(phases, PhaseGeneration):
            phases = phases.model_dump_json()
        session.phases_obj = phases
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    
    except Exception as e:
        print("Error with updating session phases_obj: ", e)
        return False
    
def insert_goal(goal_data, prereq_data, user_id, db: Session=Depends(get_db)): # anytime we insert goal, it would be from chat session objs
    
    try:
        db_goal = Goal(
            title=goal_data["title"],
            metric=goal_data["metric"],
            purpose=goal_data["purpose"],
            deadline=goal_data["deadline"],
            owner_id=user_id,

            skill_level=prereq_data["skill_level"],
            related_experience=prereq_data["related_experience"],
            resources_available=prereq_data["resources_available"],
            user_gap_assessment=prereq_data["user_gap_assessment"],
            possible_gap_assessment=prereq_data["possible_gap_assessment"],
            
            time_commitment_per_week_hours=prereq_data["time_commitment_per_week_hours"],
            budget=prereq_data["budget"],
            required_equipment=prereq_data["required_equipment"],
            support_system=prereq_data["support_system"],

            blocked_time_blocks=prereq_data["blocked_time_blocks"],
            available_time_blocks=prereq_data["available_time_blocks"],
            dependencies=prereq_data["dependencies"],
        )

        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        
        return db_goal
    except Exception as e:
        print("error with inserting goals: ", e)
        return False

def insert_phases(phases_data, goal_id, db: Session=Depends(get_db)):
    try:
        db_phases_list = []
        
        for phase in phases_data["phases"]:

            db_phase = Phase(
                title=phase["title"],
                description=phase["description"],
                start_date=phase["start_date"],
                estimated_end_date=phase["end_date"],
                goal_id=goal_id,
            )
            db_phases_list.append(db_phase)

        db.add_all(db_phases_list)
        db.commit()
        
        for db_phase in db_phases_list:
            db.refresh(db_phase)
            
        return db_phases_list
    except Exception as e:
        print("error with inserting phases: ", e)
        return False

def get_llm_response(session: ChatSession, user_input: str, db: Session=Depends(get_db)):
    responseSchema = FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration
    client = genai.Client(api_key=GOOGLE_API_KEY)
    DATE_FORMAT = '%Y-%m-%d'
    current_date_str = date.today().strftime(DATE_FORMAT)
    chat_history = pickle.loads(session.session_data)
    new_user_message = Content(
        parts=[Part.from_text(text=user_input)],
        role='user'
    )
    chat_history.append(new_user_message)
    return client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents = chat_history,
        config={
            "system_instruction": SYSTEM_INSTRUCTION.format(
                current_date_str=current_date_str,
                followUp=FollowUp.model_json_schema(),
                definitionsCreate=DefinitionsCreate.model_json_schema(),
                goalPrerequisites=GoalPrerequisites.model_json_schema(),
                currentState=CurrentState.model_json_schema(),
                fixedResources=FixedResources.model_json_schema(),
                constraints=Constraints.model_json_schema(),
                phaseGeneration=PhaseGeneration.model_json_schema(),
            ),
            "response_mime_type": "application/json",
            "response_schema": responseSchema,
        },
    )

def parse_response(response):
    models = TypeAdapter(FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration)
    text = response.candidates[0].content.parts[0].text
    # code fence removal
    if text.startswith("```"): 
        if text.startswith("```json\n"):
            text = text[8:]
        else:
            text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
        
    text = text.strip()
    return models.validate_python(json.loads(text))

def update_session_chat_history(session: ChatSession, user_input, response, db: Session=Depends(get_db)):
    chat_history = pickle.loads(session.session_data)
    new_user_message = Content(
        parts=[Part.from_text(text=user_input)],
        role='user'
    )
    chat_history.append(new_user_message)
    chat_history.append(response.candidates[0].content)
    update_session_data(session, chat_history, db)