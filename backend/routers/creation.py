import datetime, pickle, json
from datetime import date
from typing import Union, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, TypeAdapter, Field
from sqlalchemy.orm import Session, joinedload

from backend.utils import hash_password, get_current_user
from backend.db import get_db

from backend.models import User, ChatSession, Goal, Phase, Daily
from backend.schemas import (FollowUp, DefinitionsCreate, 
                            CurrentState, FixedResources, Constraints, GoalPrerequisites, 
                            PhaseGeneration, PhaseCreate,
                            DailiesGeneration, DailiesPost)
from backend.utils.system_instruction import SYSTEM_INSTRUCTION, DAILIES_GENERATION_PROMPT

from google import genai
from google.genai.types import Content, Part

import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class APIResponse(BaseModel):
    phase_tag: Literal["define_goal", "get_prerequisites", "refine_phases", "generate_dailies"]
    ret_obj: Union[FollowUp , DefinitionsCreate , GoalPrerequisites , PhaseGeneration, DailiesPost]
#APIResponse = Union[FollowUp , DefinitionsCreate , GoalPrerequisites , PhaseGeneration]

class APIRequest(BaseModel):
    user_id: int | None = None
    user_input: str

class ConfirmRequest(BaseModel):
    user_id: int | None = None
    confirm_obj: DefinitionsCreate | GoalPrerequisites | PhaseGeneration | DailiesGeneration # goal prereq only used by backend to transition

client = genai.Client(api_key=GOOGLE_API_KEY)
router = APIRouter(prefix="/create", tags=["Goals"])

@router.post("/load", response_model=APIResponse)
def load(request: APIRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    print(request)
    if request.user_id == None or request.user_id == -1 or request.user_id != user_id:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        #change_user_session(request.user_id, db) # FOR TESTING ONLY
        last_response = get_model_latest_response(request.user_id, db)
        if last_response == None:
            default = FollowUp(status='follow_up_required', question_to_user="What would you like to achieve today?")
            return APIResponse(phase_tag="define_goal", ret_obj=default)
        user_db_session = get_user_session(request.user_id, db)
        if user_db_session.phase_tag == "generate_dailies":
            dailies_obj = DailiesGeneration.model_validate_json(user_db_session.dailies_obj)
            curr_phase = dailies_obj.dailies[-1].phase_title
            user_phases = PhaseGeneration.model_validate_json(user_db_session.phases_obj)
            phase_titles = [p.title for p in user_phases.phases]
            ret_obj = DailiesPost(**(dailies_obj.model_dump()), goal_phases=phase_titles, curr_phase=curr_phase)
            return APIResponse(phase_tag="generate_dailies", ret_obj=ret_obj)
        return APIResponse(phase_tag=user_db_session.phase_tag, ret_obj=last_response)

@router.post("/query", response_model=APIResponse)
def query(request: APIRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.user_id == None or request.user_id != user_id:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        user_db_session = get_user_session(request.user_id, db)
        response_raw = get_llm_response(user_db_session, request.user_input, db)
        response_parsed = parse_response(response_raw)
        update_session_chat_history(user_db_session, request.user_input, response_raw, db)
        db.commit()

        if isinstance(response_parsed, GoalPrerequisites): # auto transition
            confirm_request = ConfirmRequest(user_id=request.user_id, confirm_obj=response_parsed)
            return confirm(confirm_request, db)
        
        elif isinstance(response_parsed, PhaseGeneration):
            update_session_phase_tag(user_db_session, "refine_phases", db)
        return APIResponse(phase_tag=user_db_session.phase_tag, ret_obj=response_parsed)
    
@router.post("/confirm", response_model=APIResponse)
def confirm(request: ConfirmRequest, user_id = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.user_id == None or request.user_id != user_id:
        raise HTTPException(status_code=500, detail=f"User not signed in")
        
    else:
        user_db_session = get_user_session(request.user_id, db)
        if isinstance(request.confirm_obj, DefinitionsCreate):
            update_session_goal(user_db_session, request.confirm_obj, db)
            update_session_phase_tag(user_db_session, "get_prerequisites", db)
            transition = APIRequest(user_id=request.user_id, user_input=f'My goal is {request.confirm_obj.model_dump_json()}\nWhat prerequisites do you need from me?')
            return query(transition, db)
        elif isinstance(request.confirm_obj, GoalPrerequisites):
            update_session_prereq(user_db_session, request.confirm_obj, db)
            update_session_phase_tag(user_db_session, "refine_phases", db)
            transition = APIRequest(user_id=request.user_id, user_input=f'My goal is {user_db_session.goal_obj}\nMy prerequisites are {request.confirm_obj.model_dump_json()}\nWhat should the plan look like?')
            return query(transition, db)
        elif isinstance(request.confirm_obj, PhaseGeneration): # and user_db_session.phase_tag != "refine_phases": forgot why i added this condition.
            update_session_phases(user_db_session, request.confirm_obj, db)
            update_session_phase_tag(user_db_session, "generate_dailies", db)

            phase_titles = [p.title for p in request.confirm_obj.phases]
            new_dailies = generate_dailies(user_db_session, request.confirm_obj.phases[0], db)
            update_session_dailies(user_db_session, new_dailies, db)
            ret_obj = DailiesPost(**(new_dailies.model_dump()), goal_phases=phase_titles, curr_phase=request.confirm_obj.phases[0].title)
            return APIResponse(phase_tag="generate_dailies", ret_obj=ret_obj)
        elif isinstance(request.confirm_obj, DailiesGeneration):
            update_session_dailies(user_db_session, request.confirm_obj, db)
            curr_phase = request.confirm_obj.dailies[-1].phase_title
            user_phases = PhaseGeneration.model_validate_json(user_db_session.phases_obj)

            if curr_phase == user_phases.phases[-1].title: # last daily is from the final phase -- goal is completed
                goal_json = json.loads(user_db_session.goal_obj)
                prereq_json = json.loads(user_db_session.prereq_obj)
                phases_json = json.loads(user_db_session.phases_obj)
                goal_db = insert_goal(goal_json, prereq_json, request.user_id, db)
                db_phases_list = insert_phases(phases_json, goal_db.id, db)
                insert_dailies(request.confirm_obj, db_phases_list, db)
                change_user_session(request.user_id, db)
                return load(APIRequest(user_id=request.user_id, user_input=""), db)
            else: # transition to generating next phase's dailies
                phase_titles = [p.title for p in user_phases.phases]
                next_phase = phase_titles.index(curr_phase)+1
                
                new_dailies = generate_dailies(user_db_session, user_phases.phases[next_phase], db)
                update_session_dailies(user_db_session, new_dailies, db)

                ret_obj = DailiesPost(**(new_dailies.model_dump()), goal_phases=phase_titles, curr_phase=phase_titles[next_phase])
                return APIResponse(phase_tag="generate_dailies", ret_obj=ret_obj)

def generate_dailies(session: ChatSession, phase: PhaseCreate, db: Session=Depends(get_db)):

    all_phases_dailies = []
    if session.dailies_obj:
        all_phases_dailies = DailiesGeneration.model_validate_json(session.dailies_obj).dailies
    
    current_planning_date = phase.start_date
    print(f"phase: {phase.title}, start date: {phase.start_date}, end date: {phase.end_date}")
    while current_planning_date <= phase.end_date:
        if current_planning_date > phase.end_date:
                break
        
        dailies_generation_prompt = f"""My goal is {session.goal_obj}
                                        My prerequisites are {session.prereq_obj}
                                        The overall plan is {session.phases_obj}
                                        The current phase to plan for is {phase.title}
                                        The currently confirmed tasks for this goal (for context and continuity) is: {all_phases_dailies}.
                                        Generate the daily schedule for the next 2 weeks starting from, and including {current_planning_date}
                                        """
        
        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents = [{
                "role": "user", 
                "parts": [{"text": f"{dailies_generation_prompt}"}]
            }],
            config={
                "system_instruction": DAILIES_GENERATION_PROMPT.format(dailiesGeneration=DailiesGeneration.model_json_schema()),
                "response_mime_type": "application/json",
                "response_schema": DailiesGeneration,
            },
        )
        response = parse_response(response)
        new_tasks = response.dailies
        print(new_tasks)
        valid_new_tasks = [t for t in new_tasks if t.dailies_date <= phase.end_date]
        all_phases_dailies.extend(valid_new_tasks)
        if valid_new_tasks != []:
            last_task_date = max(t.dailies_date for t in valid_new_tasks)
            current_planning_date = last_task_date + datetime.timedelta(days=1)
        else:
            current_planning_date += datetime.timedelta(days=14)
    
    print(all_phases_dailies)
    return DailiesGeneration(status="dailies_generated", dailies=all_phases_dailies)
    

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
        db.refresh(user)
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
    models = TypeAdapter(FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration | DailiesGeneration)
    session = get_user_session(uid, db)
    chat_history = pickle.loads(session.session_data)
    if len(chat_history) == 0:
        return None
    text_obj = json.loads(chat_history[-1].parts[0].text)
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
    
def update_session_data(session: ChatSession, session_data, db: Session=Depends(get_db)):
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
        db.rollback() 
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
        db.rollback() 
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
        db.rollback() 
        return False

def update_session_dailies(session: ChatSession, dailies, db: Session=Depends(get_db)):
    try:
        if isinstance(dailies, DailiesGeneration):
            dailies = dailies.model_dump_json()
        session.dailies_obj = dailies
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return True
    
    except Exception as e:
        print("Error with updating session phases_obj: ", e)
        db.rollback() 
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
        )

        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        
        return db_goal
    except Exception as e:
        print("error with inserting goals: ", e)
        db.rollback() 
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
        db.rollback() 
        return False

def insert_dailies(dailies_data: DailiesGeneration, db_phases_list, db: Session=Depends(get_db)):
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
    
def get_llm_response(session: ChatSession, user_input: str, db: Session=Depends(get_db)):
    responseSchema = FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration
    client = genai.Client(api_key=GOOGLE_API_KEY)
    DATE_FORMAT = '%Y-%m-%d'
    current_date_str = date.today().strftime(DATE_FORMAT)
    chat_history = pickle.loads(session.session_data)
    
    new_user_message = Content(
        parts=[Part.from_text(text=f'CURRENT_PHASE = "{session.phase_tag}"\n{user_input}')],
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
                dailiesGeneration=DailiesGeneration.model_json_schema(),
            ),
            "response_mime_type": "application/json",
            "response_schema": responseSchema,
        },
    )

def parse_response(response): # can do more parsing but thats kinda a lot of work i.e. check for missing fields
    models = TypeAdapter(FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration | DailiesGeneration)
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
        parts=[Part.from_text(text=f'CURRENT_PHASE = "{session.phase_tag}"\n{user_input}')],
        role='user'
    )
    chat_history.append(new_user_message)
    chat_history.append(response.candidates[0].content)
    update_session_data(session, chat_history, db)
