import os
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types
from datetime import date
from typing import Union
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import select, delete, update

from backend.db import get_db
from backend import models, schemas, prompts, utils
from utils.db_utils import add_message_to_history, get_chat_history, get_last_message, get_user_session_details, clear_chat_history, reset_session
from prompts import DAILIES_GENERATION_INSTRUCTIONS, DEFINITION_INSTRUCTION, PHASE_GENERATION_INSTRUCTION, PHASE_REFINEMENT_INSTRUCTION, GOAL_PREREQUISITE_INSTRUCTION
from models import ChatSession, ChatHistory
from models import User
from models import Goal, Prerequisite, Phase
from schemas import (
    GoalRequest, GoalConfirm, FollowUp, DefinitionsCreate, DefinitionsBase, GoalPrerequisites,
    PhaseGeneration, DailyTaskGeneration
)

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

ResponseSchema = {1: Union[DefinitionsCreate, FollowUp], 2: Union[GoalPrerequisites, FollowUp], 3: PhaseGeneration, 4: DailyTaskGeneration}
APIResponse = Union[FollowUp, DefinitionsCreate, PhaseGeneration]
router = APIRouter(prefix="/create", tags=["Create"])

# initial click will lead to '/load'
# when phase=1 and chat history is empty, returns followUp("What do you want to achieve today?")
# if not, returns latest_model_reponse.parsed
# in phase 1, all user text responses (GoalRequest) will lead to '/query'
# the back end should return followUp() or DefinitionsCreate()
# on DefinitionsCreate(), user will edit and post a GoalConfirm object
# backend to transition to phase 2 ==> update chat session to link to a newly created goal, and clear chat history. current_phase to be changed to 2.
# returns a followUp()
# frontend will post GoalRequests until backend llm decides to transition.
# the llm returns GoalPrerequisites Obj
# backend will populate the GoalPrerequisites, update current phase, clear chat history
# backend then returns a PhaseGeneration Obj
# frontend gets either user comments (GoalRequest to '/query') or Confirmation (GoalConfirm to '/confirm')
# backend will always return a PhaseGeneration Obj with new comments
# on confirm transition to phase 4, for now, we will end the conversation, add the phases to the db, mark the goal as completed, and reset the chat back to phase 1


# Frontend has 4 different displays based on apiresponse (sees obj type from status):
# FollowUp # displays question to user
# DefinitionsCreate # displays sumamry, posts to confirm
# PhaseGeneration  # displays proposed phases, either posts to query or confirm
# Dailies # displays dailies for user to edit and confirm
def get_user_session_details(user_id, db: Session = Depends(get_db)):
    session_id, phase, goal_id = db.query(
        ChatSession.session_id,
        ChatSession.current_phase,
        ChatSession.goal_id
    ).select_from(User).join(
        ChatSession, User.current_session == ChatSession.session_id
    ).filter(
        User.id == user_id
    ).first()

    return session_id, phase, goal_id

@router.post("/load", response_model=APIResponse)
def load(user_id, db: Session = Depends(get_db)):
    """
    This is the single source of truth for loading the frontend.
    It reads the current state and returns the correct Pydantic object.
    
    Logic:
    1. Phase 1: New session? -> Welcome prompt. In progress? -> Last model reply.
    2. Phase 2: transition -> default user input to llm, response stored. -> Last model reply.
    3. Phase 3: In progress? -> Current plan review.
    """
    session_details = get_user_session_details(db, user_id)
    history = get_last_message(db, session_details.session_id)
    
    if session_details.current_phase == 1:
        if not history:
            return FollowUp(status="follow_up_required", message="What do you want to achieve today?" )
    
    return history[-1] # needs parsing, check status

@router.post("/query", response_model=APIResponse)
def query(request: GoalRequest, db: Session = Depends(get_db)):
    """
    Handles all text-based requests
    
    1. Adds the user's message to the chat history.
    2. Calls the LLM for a response (based on state).
    3. Handles any state transitions (e.g., phase change).
    4. Returns the new state to the frontend.
    """
    session_details = get_user_session_details(db, request.user_id)
    if not session_details:
        raise HTTPException(status_code=404, detail="User session not found")

    add_message_to_history(db, session_details.session_id, "user", request.user_input)
    llm_response = get_llm_response(db, session_details.session_id, session_details.current_phase)
    
    process_llm_action(db, request.user_id, session_details, llm_response)
    db.commit()
    
    return load(request.user_id, db)

@app.post("/confirm", response_model=APIResponse)
def handle_confirmation(data: GoalConfirm, db: Session = Depends(get_db), user_id: int = Depends(get_db)):
    """
    Handles user confirmation of a generated plan (Goal or Phases).
    
    This endpoint:
    1. Identifies the current phase to know WHAT is being confirmed.
    2. Calls the appropriate helper to transition the state.
    3. Returns the new state.
    """
    session_details = get_user_session_details(db, user_id)
    if not session_details:
        raise HTTPException(status_code=404, detail="User session not found")

    success = process_user_confirmation(db, user_id, session_details, data)

    if not success:
        raise HTTPException(status_code=400, detail="Confirmation failed or was invalid for the current phase.")
    return load(db, user_id)

@router.post("/reset", response_model=APIResponse)
def reset(user_id, db: Session = Depends(get_db)):
    if reset_session(db, user_id):
        db.commit()
        return load(user_id)

########################################################################
# YOU CAN IGNORE THESE
########################################################################
def get_prompt(session_id, db: Session = Depends(get_db)):
    query = (
        select(ChatHistory.content)
        .where(
            ChatHistory.session_uid == session_id,
            ChatHistory.role == 'prompt'
        )
    )
    return db.execute(query).one()

def get_model_response(session_id, phase, user_input, db: Session = Depends(get_db)):
    history = get_history(session_id)
    history.append(
        types.Content(
            role='user', 
            parts=[types.Part.from_text(user_input)]
        )
    )
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents = history,
        config={
            "system_instruction": get_prompt(session_id),
            "response_mime_type": "application/json",
            "response_schema": ResponseSchema[phase],
        },
    )
    return response

@router.post("/query", response_model=schemas.APIResponse)
def llm_query(goal_request: schemas.GoalRequest, db: Session = Depends(get_db)): # session already exists
    session_id = goal_request.session_id
    user_input = goal_request.user_input
    raw = get_model_response(session_id, phase, user_input)
    model_text = raw.candidates[0].content.parts[0].text
    response = raw.parsed
    if phase == 2 and isinstance(response, DefinitionsCreate):
        return confirm()

    max_index = (
        select(func.max(ChatHistory.text_num))
        .where(ChatHistory.session_uid == session_id)
    )
    last_text_num = db.execute(max_index).scalar_one_or_none() or -1

    user_text_num = last_text_num + 1
    model_text_num = user_text_num + 1

    user_history_entry = ChatHistory(session_uid=session_id, text_num=user_text_num, role='user', content=user_input)
    db.add(user_history_entry)
    model_history_entry = ChatHistory(session_uid=session_id, text_num=model_text_num, role='model', content=model_text)
    db.add(model_history_entry)
    db.commit()

    return response

@router.post("/confirm", response_model=schemas.APIResponse)
def confirm(phase_details: GoalConfirm, db: Session = Depends(get_db)): # transition to another phase
    curr_phase = phase_details.phase
    goal_id = phase_details.goal_id
    session_id = phase_details.session_id
    data = phase_details.data
    goal_id = update_db(data, curr_phase, goal_id) # unpack json and commit to db
    new_phase = update_session(session_id) # delete old chat history
    llm_data = initialise_llm(goal_id, session_id, new_phase)
    return APIResponse(session_id=session_id, phase=new_phase, goal_id=goal_id, data=llm_data)

def update_db(data, phase, goal_id):
    if phase == 1:
        return create_new_goal(goal_id, data)
    if phase == 2:
        return update_goal_prerequisites(goal_id, data)
    if phase == 3:
        return update_phase_generation(goal_id, data)
    
def create_new_goal(user_id: int, definitions: DefinitionsBase, db: Session = Depends(get_db)):
    try: 
        user_exists = db.execute(
            select(User.id).where(User.id == user_id)
        ).scalar_one_or_none()
        
        if not user_exists:
            print(f"Error: User ID {user_id} not found. Cannot create goal.")
            db.rollback()
            return None
        
        goal_data = definitions.model_dump(mode='json')
        new_goal = Goal(user_id=user_id, **goal_data)
        db.add(new_goal)
        db.commit()
        new_goal_id = new_goal.id
        return new_goal_id
    except:
        db.rollback()
        return None

def update_goal_prerequisites(goal_id: int, prerequisites: GoalPrerequisites, db: Session = Depends(get_db)):
    try:
        prereqs_json = prerequisites.model_dump_json(indent=2)
        prereq_update = (
            update(Goal)
            .where(Goal.id == goal_id)
            .values(prerequisites_json=prereqs_json)
        )
        
        result = db.execute(prereq_update)
        if result.rowcount == 0:
            print(f"Error: Goal ID {goal_id} not found. No update performed.")
            db.rollback()
            return None
            
        db.commit()
        return goal_id
        
    except:
        db.rollback()
        return None

def update_phase_generation(goal_id: int, phase_generation: PhaseGeneration,  db: Session = Depends(get_db)):
    try:
        delete_phases = delete(Phase).where(Phase.goal_id == goal_id)
        db.execute(delete_phases)
        
        new_phases_data = [
            Phase(
                goal_id=goal_id,
                title=phase.title,
                description=phase.description,
                start_date=phase.start_date,
                end_date=phase.end_date
            )
            for phase in phase_generation.phases
        ]
        
        db.add_all(new_phases_data)
        db.commit()
        return goal_id
        
    except:
        db.rollback()
        return None
    
def update_session(session_id, db: Session = Depends(get_db)):
    delete_history = (
        delete(ChatHistory)
        .where(ChatHistory.session_uid == session_id)
    )
    db.execute(delete_history)
        
    update_session = (
        update(ChatSession)
        .where(ChatSession.session_uid == session_id)
        .values(current_phase=ChatSession.current_phase + 1)
    )
    db.execute(update_session)
    db.commit()
    return ChatSession.current_phase + 1

def initialise_llm(goal_id, session_id, phase, db: Session = Depends(get_db)):
    if phase == 1:
        prompt = system_instructions = DEFINITION_INSTRUCTION.format(current_date_str=date.today().strftime('%Y-%m-%d'), followUp=FollowUp.model_json_schema(), definitionsCreate=DefinitionsCreate.model_json_schema())
        response = FollowUp(status="follow_up_required", question_to_user="I want to: ")
    elif phase == 2:
        goals_string = get_goal_details(goal_id)
        prompt = system_instructions = GOAL_PREREQUISITE_INSTRUCTION.format(current_date_str=date.today().strftime('%Y-%m-%d'), followUp=FollowUp.model_json_schema(), goalPrerequisites=GoalPrerequisites.model_json_schema())
        user_input = goals_string
        user_history_entry = ChatHistory(session_uid=session_id, text_num=1, role='user', content=user_input)
        db.add(user_history_entry)
    elif phase == 3:
        goals_string = get_goal_details(goal_id)
        system_instructions = PHASE_GENERATION_INSTRUCTION.format(current_date_str=date.today().strftime('%Y-%m-%d'), goal=goals_string, phaseGeneration=PhaseGeneration.model_json_schema())
        user_input="Generate the most effective plan to achieve my goals given the prerequisites and constraints"
        
        prompt = PHASE_REFINEMENT_INSTRUCTION.format(current_date_str=date.today().strftime('%Y-%m-%d'), goal=goals_string, phaseGeneration=PhaseGeneration.model_json_schema())
        #"With the current plan of {initial.phases}, I think that {usr_input}"

    if phase != 1:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents = [types.Content(role='user', parts=[types.Part.from_text(user_input)])],
            config={
                "system_instruction": system_instructions,
                "response_mime_type": "application/json",
                "response_schema": ResponseSchema[phase],
            },
        )

    prompt_history_entry = ChatHistory(session_uid=session_id, text_num=0, role='prompt', content=prompt)
    db.add(prompt_history_entry)
    db.commit()

    return response
    
def get_goal_details(goal_id: int, db: Session = Depends(get_db)):
    try:
        goal = db.scalars(select(Goal).where(Goal.id == goal_id)).first()

        if not goal:
            print(f"Goal ID {goal_id} not found.")
            return None

        prerequisites_data = None
        if goal.prerequisites_json:
            try:
                # Deserialize the JSON string back into the Pydantic model
                prereqs_dict = json.loads(goal.prerequisites_json)
                prerequisites_data = GoalPrerequisites.model_validate(prereqs_dict)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Failed to parse prerequisites_json for Goal ID {goal_id}: {e}")

        summary = [
            f"--- Goal Definitions ---",
            f"Title: {goal.title}",
            f"Metric: {goal.metric}",
            f"Purpose: {goal.purpose}",
            f"Deadline: {goal.deadline.strftime('%Y-%m-%d')}",
        ]

        if prerequisites_data:
            state = prerequisites_data.current_state
            resources = prerequisites_data.fixed_resources
            constraints = prerequisites_data.constraints
            
            summary.extend([
                "\n--- Current State & Prerequisites ---",
                f"Status: {prerequisites_data.status.replace('_', ' ').title()}",
                f"Skill Level: {state.skill_level}",
                f"Related Experience: {state.related_experience}",
                f"Resources Available: {state.resources_available}",
                f"User Gaps Assessed: {', '.join(state.user_gap_assessment) or 'None'}",
                f"Commitment (Weekly Hours): {resources.time_commitment_per_week_hours} hours",
                f"Budget: {resources.budget}",
                f"Required Equipment: {resources.required_equipment}",
                f"Support System: {resources.support_system}",
                f"Blocked Times: {', '.join(constraints.blocked_time_blocks) or 'None'}",
                f"Available Times: {', '.join(constraints.available_time_blocks) or 'None'}",
            ])

        return "\n".join(summary)

    except Exception as e:
        print(f"Failed to generate goal summary string for ID {goal_id}: {e}")
        return None