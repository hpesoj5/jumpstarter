import datetime, pickle, json
from datetime import date

from fastapi import Depends, HTTPException
from pydantic import TypeAdapter
from sqlalchemy.orm import Session, joinedload

from google.genai.types import Content, Part

from backend.utils import (hash_password,
                           
                           )
from backend.db import get_db

from backend.models import User, ChatSession, Goal, Phase, Daily
from backend.schemas import (FollowUp,
                            DefinitionsCreate,
                            GoalPrerequisites, 
                            PhaseGeneration,
                            DailiesGeneration,
                            DailiesPost)

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
    
def insert_user(username, email, password, db: Session=Depends(get_db)): # insert new user into db
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

def change_user_session(uid, db: Session=Depends(get_db)): # creates new session and updates user to a new session
    try:
        user = db.get(User, uid)
        new_session = insert_session(db)
        user.session = new_session
        db.commit()
        db.refresh(user)
        print(f"User {user.username} (uid: {uid}), successfully updated session")
        return new_session

    except Exception as e:
        print(e)
        return False
    
def get_user_session(uid, db: Session=Depends(get_db)) -> ChatSession: # returns the entire user session object
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

def get_model_latest_response(uid, db: Session=Depends(get_db)): # returns last message in chat history
    models = TypeAdapter(FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration | DailiesGeneration)
    session = get_user_session(uid, db)
    chat_history = pickle.loads(session.session_data)
    if len(chat_history) == 0:
        return None
    text_obj = json.loads(chat_history[-1])
    return models.validate_python(text_obj)

def update_session_phase_tag(session: ChatSession, phase_tag, db: Session=Depends(get_db)):
    try:
        session.phase_tag = phase_tag
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    except Exception as e:
        print("Error with updating session data: ", e)
        db.rollback() 
        return False
    
def update_session_data(session: ChatSession, session_data, db: Session=Depends(get_db)): # updates the pickled chat object
    try:
        session.session_data = pickle.dumps(session_data)
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    except Exception as e:
        print("Error with updating session data: ", e)
        db.rollback() 
        return False
    
def update_session_chat_history(session: ChatSession, user_input, response, db: Session=Depends(get_db)):
    chat_history = pickle.loads(session.session_data)

    new_user_message = {
        'role': 'user',
        'content': f'CURRENT_PHASE = "{session.phase_tag}"\n{user_input}',
    }

    chat_history.append(new_user_message)
    new_reponse = {
        'role': 'assistant',
        'content': response,
    }
    chat_history.append(new_reponse['content'].output[1].content[0].text)
    
    update_session_data(session, chat_history, db)

def update_session_goal(session: ChatSession, goal, db: Session=Depends(get_db)): # after user completes goal_def phase, dump the DefinitionsCreate object into the session
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
        db.rollback() 
        return False
    
def update_session_prereq(session: ChatSession, prereq, db: Session=Depends(get_db)): # after user completes prereq phase, dump the GoalPrerequisites object into the session
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
        db.rollback() 
        return False

def update_session_phases(session: ChatSession, phases, db: Session=Depends(get_db)): # after user completes phase_gen phase, dump the PhaseGeneration object into the session
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
        db.rollback() 
        return False

def update_session_dailies(session: ChatSession, dailies, db: Session=Depends(get_db)): # each time use confirms the dailies for given phase, update the new set of all dailies
    try:
        if isinstance(dailies, DailiesPost):
            dailies = json.dumps(dailies.model_dump(mode="json")) # nested pydantic models
        session.dailies_obj = dailies
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    
    except Exception as e:
        print("Error with updating session phases_obj: ", e)
        db.rollback() 
        return False

def insert_goal(goal_data, prereq_data, user_id, db: Session=Depends(get_db)): # inserts goal into db table. anytime we insert goal, it would be from chat session objs
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
        )

        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        
        return db_goal
    except Exception as e:
        print("error with inserting goals: ", e)
        db.rollback() 
        return False

def insert_phases(phases_data, goal_id, db: Session=Depends(get_db)): # insert phases into phase table. same logic as insert_data
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
        db.rollback() 
        return False

def insert_dailies(dailies_data: DailiesPost, db_phases_list, db: Session=Depends(get_db)): # insert dailies into dailies table. same logic as insert_data
    try:
        phase_title_to_id = {
            phase.title: phase.id 
            for phase in db_phases_list
        }
        
        db_dailies_list = []
        
        for daily_task in dailies_data.dailies:
            
            phase_title = daily_task.phase_title
            phase_id = phase_title_to_id.get(phase_title)
            
            if phase_id is None:
                print(f"Error: Could not find Phase ID for title: {phase_title}")
                continue
            
            db_daily = Daily(
                task_description=daily_task.task_description,
                dailies_date=daily_task.dailies_date,
                start_time=daily_task.start_time,
                estimated_time_minutes=daily_task.estimated_time_minutes,
                phase_id=phase_id,
            )
            db_dailies_list.append(db_daily)

        db.add_all(db_dailies_list)
        db.commit()
        
        for db_daily in db_dailies_list:
            db.refresh(db_daily)
            
        return db_dailies_list
        
    except Exception as e:
        print("Error with inserting dailies: ", e)
        db.rollback() 
        return False