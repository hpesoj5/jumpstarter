import datetime
from datetime import date
import pickle
import json

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, joinedload

from backend.utils import hash_password
from backend.db import get_db

from backend.models import User, ChatSession, Goal, Phase, Daily
from backend.schemas import (FollowUp, DefinitionsCreate, 
                            CurrentState, FixedResources, Constraints, GoalPrerequisites, 
                            PhaseGeneration, PhaseCreate)
from backend.utils.system_instruction import SYSTEM_INSTRUCTION

from google import genai
from google.genai.chats import Chat
from google.genai.types import UserContent, Content, Part

import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve()
load_dotenv("backend\\.env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class APIResponse(BaseModel):
    session_id: str
    data: FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration  

class APIRequest(BaseModel):
    user_input: str
    user_id: str | None = None
    phase: str

def insert_session(db: Session=Depends(get_db)): # will not commit in this function. commits should happen with what calls it.
    try:
        responseSchema = FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration
        client = genai.Client(api_key=GOOGLE_API_KEY)
        DATE_FORMAT = '%Y-%m-%d'
        current_date_str = date.today().strftime(DATE_FORMAT)
        chat = client.chats.create(
            model='gemini-2.5-flash-lite',
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
        print(chat.get_history())
        new_session = ChatSession(session_data=pickle.dumps(chat.get_history()))
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
        return True

    except Exception as e:
        print(e)
        return False
    
def get_user_session(uid, db: Session=Depends(get_db)) -> ChatSession: 
    try:
        user = db.query(User).options(
            joinedload(User.session)
        ).filter(User.id == uid).first()
        
        if not user:
            print(f"User with ID {uid} not found.")
            return False
        
        if not user.session:
            print(f"User {uid} does not have an active session.")
            return False
        return user.session
    
    except Exception as e:
        print(e)
        return False

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

goal_pydantic = DefinitionsCreate(status='definitions_extracted', 
                                  title='Build a goal setting and tracking app', 
                                  metric='Track user progress within the app', # faulty metric, may need to look into this
                                  purpose='To help users set and achieve their goals with the assistance of an integrated LLM for setting SMART goals and planning.', 
                                  deadline=datetime.date(2026, 11, 20)
                                )
goal_json = {"status":"definitions_extracted","title":"Build a goal setting and tracking app","metric":"Track user progress within the app","purpose":"To help users set and achieve their goals with the assistance of an integrated LLM for setting SMART goals and planning.","deadline":"2026-11-20"}

prereq_pydantic = GoalPrerequisites(blocked_time_blocks=[],
                                    available_time_blocks=['Monday-Friday 6pm-8pm', 'Saturday-Sunday 9am-9pm'],
                                    dependencies=[],
                                    time_commitment_per_week_hours=12.0, 
                                    budget=0.0,
                                    required_equipment=[],
                                    support_system=['Friends as coding partners'], 
                                    skill_level='Beginner (experience with Tailwind and pure JS/CSS, but not React)' ,
                                    related_experience=[] ,
                                    resources_available=['PostgreSQL', 'Node.js', 'Python', 'Alembic', 'Laptop for development', 'Cloud hosting'],
                                    user_gap_assessment=['Lack of React experience', 'Need to research specific frameworks/libraries'],
                                    possible_gap_assessment=['Familiarity with LLM integration', 'Database schema design for user progress tracking', 'UI/UX design for a goal-setting app', 'Deployment and scaling strategies'],
                                    status='prerequisites_extracted'
                                    )
prereq_json = {"blocked_time_blocks":[],"available_time_blocks":["Monday-Friday 6pm-8pm","Saturday-Sunday 9am-9pm"],"dependencies":[],"time_commitment_per_week_hours":12.0,"budget":0.0,"required_equipment":[],"support_system":["Friends as coding partners"],"skill_level":"Beginner (experience with Tailwind and pure JS/CSS, but not React)","related_experience":[],"resources_available":["PostgreSQL","Node.js","Python","Alembic","Laptop for development","Cloud hosting"],"user_gap_assessment":["Lack of React experience","Need to research specific frameworks/libraries"],"possible_gap_assessment":["Familiarity with LLM integration","Database schema design for user progress tracking","UI/UX design for a goal-setting app","Deployment and scaling strategies"],"status":"prerequisites_extracted"}
phases_pydantic=PhaseGeneration(status='phases_generated', 
                                phases=[ # consider changing the class (and prompt) such that target and description are seperate
                                    PhaseCreate(title='Foundation and Skill Development', 
                                                description='Set up the project environment, establish basic app architecture, and begin learning/implementing React. Develop core UI components and set up basic routing. Target: A functional basic app structure with a learn React module completed.', 
                                                start_date=datetime.date(2025, 11, 20), 
                                                end_date=datetime.date(2026, 2, 20)), 
                                    PhaseCreate(title='Core Feature Implementation', 
                                                description='Implement the primary goal-setting and tracking features. Integrate the LLM for SMART goal generation and planning. Focus on building the backend for data storage and user management. Target: Core features for goal setting, planning, and basic progress tracking are functional.', 
                                                start_date=datetime.date(2026, 2, 21), 
                                                end_date=datetime.date(2026, 7, 20)), 
                                    PhaseCreate(title='Advanced Features and LLM Integration', 
                                                description='Refine LLM integration for personalized feedback and advanced planning. Implement detailed progress tracking visualizations and user reporting. Develop and integrate any remaining features from the user gap assessment. Target: Comprehensive progress tracking and advanced LLM functionalities are integrated.', 
                                                start_date=datetime.date(2026, 7, 21), end_date=datetime.date(2026, 11, 20))
                                        ]
                                    )
phases_json = {"status":"phases_generated","phases":[{"title":"Foundation and Skill Development","description":"Set up the project environment, establish basic app architecture, and begin learning/implementing React. Develop core UI components and set up basic routing. Target: A functional basic app structure with a learn React module completed.","start_date":"2025-11-20","end_date":"2026-02-20"},{"title":"Core Feature Implementation","description":"Implement the primary goal-setting and tracking features. Integrate the LLM for SMART goal generation and planning. Focus on building the backend for data storage and user management. Target: Core features for goal setting, planning, and basic progress tracking are functional.","start_date":"2026-02-21","end_date":"2026-07-20"},{"title":"Advanced Features and LLM Integration","description":"Refine LLM integration for personalized feedback and advanced planning. Implement detailed progress tracking visualizations and user reporting. Develop and integrate any remaining features from the user gap assessment. Target: Comprehensive progress tracking and advanced LLM functionalities are integrated.","start_date":"2026-07-21","end_date":"2026-11-20"}]}

chat_history = [UserContent(
  parts=[
    Part(
      text="""CURRENT_PHASE = "define_goal"
I want to test a program"""
    ),
  ]
), Content(
  parts=[
    Part(
      text="""{
  "status": "follow_up_required",
  "question_to_user": "What specific aspect of the program do you want to test, and what would be the measurable outcome of a successful test?"
}"""
    ),
  ],
  role='model'
)]

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
conn = Session(bind=engine)
uid = 1 #insert_user(username="test", email="test@gmail.com", password="test", db=conn)
user_session = get_user_session(uid, conn)
# update_session_goal(user_session, goal_json, conn)
# update_session_prereq(user_session, prereq_json, conn)
# update_session_phases(user_session, phases_json, conn)
# db_goal = insert_goal(goal_json, prereq_json, uid, conn)
db_phases = insert_phases(phases_json, 1, conn)
# print(pickle.loads(user_session.session_data))
# update_session_data(user_session, chat_history, conn)
# print(pickle.loads(user_session.session_data))