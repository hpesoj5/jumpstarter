import os
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types
from datetime import date
from typing import Union
from sqlalchemy import select, delete, update
import json

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

def process_llm_action(db, user_id, session_details, llm_response):
    """
    Handles the side-effects of an LLM's response.
    Saves the response to history and triggers phase transitions.
    """
    if isinstance(llm_response, GoalPrerequisites): # phase 2 model transition
        return process_user_confirmation(db, user_id, session_details, goalConfirm(user_id=user_id, data=llm_response))
    
    add_message_to_history(db, session_details.session_id, "model", llm_response.model_dump_json())


def process_user_confirmation(db, user_id, session_details, goalConfirm):
    """
    Handles user confirmation of a goal or plan.
    This is where the main state transitions happen.
    """
    
    if session_details.current_phase == 1:
        handle_goal_creation_transition(db, session_details.session_id, goalConfirm)
        return True
    
    if session_details.current_phase == 2:
        handle_prerequisite_transition(db, session_details.session_id, session_details.goal_id, goalConfirm)
        return True

    if session_details.current_phase == 3:
        handle_plan_finalization(db, user_id, session_details.session_id, session_details.goal_id, goalConfirm)
        return True
    
    return False


def handle_goal_creation_transition(db, session_id, goalConfirm):
    # Create Goal in DB
    goal_data = goalConfirm.data
    new_goal = Goal(
        title=goal_data.title,
        metric=goal_data.metric,
        purpose=goal_data.purpose,
        deadline=goal_data.deadline,
        owner_id=goal_data.user_id,
        is_planning_complete=False # True only after finalised
    )
    db.add(new_goal)
    db.flush() # Commit the new goal to get its ID

    # Update ChatSession
    session_to_update = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()
    
    if session_to_update:
        session_to_update.goal_id = new_goal.id
        session_to_update.current_phase = 2
        db.add(session_to_update)
        
        # clear chat history
        clear_chat_history(db, session_id)

    goal_str = "Here is my goal: \n" + get_goal_details(goal_id=new_goal.id, db=db)
    add_message_to_history(db, session_id, "user", goal_str)
    llm_response = get_llm_response(db, session_id, current_phase)
    add_message_to_history(db, session_id, "model", llm_response.model_dump_json())

def handle_prerequisite_transition(db, session_id, goal_id, goalConfirm):
    prereq_data=goalConfirm.data
    new_prereq = Prerequisite(
        # The goal_id links the Prerequisite to the Goal
        goal_id=goal_id,
        
        # CurrentState fields
        skill_level=prereq_data.current_state.skill_level,
        related_experience=prereq_data.current_state.related_experience,
        resources_available=prereq_data.current_state.resources_available,
        user_gap_assessment=prereq_data.current_state.user_gap_assessment,
        possible_gap_assessment=prereq_data.current_state.possible_gap_assessment,
        
        # FixedResources fields
        time_commitment_per_week_hours=prereq_data.fixed_resources.time_commitment_per_week_hours,
        budget=prereq_data.fixed_resources.budget,
        required_equipment=prereq_data.fixed_resources.required_equipment,
        support_system=prereq_data.fixed_resources.support_system,
        
        # Constraints fields
        blocked_time_blocks=prereq_data.constraints.blocked_time_blocks,
        available_time_blocks=prereq_data.constraints.available_time_blocks,
        dependencies=prereq_data.constraints.dependencies
    )
    db.add(new_prereq)

    session_to_update = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()
    
    if session_to_update:
        session_to_update.current_phase = 3
        db.add(session_to_update)
        
        # clear chat history
        clear_chat_history(db, session_id)    
        
    goal_str = "Here is my goal: \n" + get_goal_details(goal_id=new_goal.id, db=db) 
    add_message_to_history(db, session_id, "user", goal_str) 
    llm_response = get_llm_response(db, session_id, current_phase) # make this into one prompt instead? idk how maintain
    add_message_to_history(db, session_id, "model", llm_response.model_dump_json())

def handle_plan_finalization(db, user_id, session_id, goal_id, goalConfirm):
    for phase in goalConfirm.data.phases:
        
        new_phase = Phase(
            goal_id=goal_id,
            title=phase.title,
            description=phase.description,
            start_date=phase.start_date,
            end_date=phase.end_date,
            is_completed=False
        )
        db.add(new_phase)
        db.flush() 
        
        # UPDATE DAILIES

    goal_update = (
        update(Goal)
        .where(Goal.id == goal_id)
        .values(is_planning_complete=True)
    )
    db.execute(goal_update)
    reset_session(db, user_id) 

def get_goal_details(goal_id, db):
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