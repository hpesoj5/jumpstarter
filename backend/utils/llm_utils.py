import datetime, pickle, json
from datetime import date

from fastapi import Depends
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from backend.db import get_db

from backend.models import ChatSession
from backend.schemas import (FollowUp,
                            DefinitionsCreate, 
                            CurrentState, FixedResources, Constraints, GoalPrerequisites, 
                            PhaseGeneration, PhaseCreate,
                            DailiesGeneration, DailiesPost,)
from backend.utils.system_instruction import SYSTEM_INSTRUCTION, DAILIES_GENERATION_PROMPT
from backend.utils.instruction_chain import BASE_INSTRUCTION, PHASE_INSTRUCTIONS

from google import genai
from google.genai.types import Content, Part

import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# def get_llm_response(session: ChatSession, user_input: str, db: Session=Depends(get_db)):
#     responseSchema = FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration
#     client = genai.Client(api_key=GOOGLE_API_KEY)
#     DATE_FORMAT = '%Y-%m-%d'
#     current_date_str = date.today().strftime(DATE_FORMAT)
#     chat_history = pickle.loads(session.session_data)
    
#     new_user_message = Content(
#         parts=[Part.from_text(text=f'CURRENT_PHASE = "{session.phase_tag}"\n{user_input}')],
#         role='user'
#     )
#     chat_history.append(new_user_message)
#     return client.models.generate_content(
#         model='gemini-2.5-flash-lite',
#         contents = chat_history,
#         config={
#             "system_instruction": SYSTEM_INSTRUCTION.format(
#                 current_date_str=current_date_str,
#                 followUp=FollowUp.model_json_schema(),
#                 definitionsCreate=DefinitionsCreate.model_json_schema(),
#                 goalPrerequisites=GoalPrerequisites.model_json_schema(),
#                 currentState=CurrentState.model_json_schema(),
#                 fixedResources=FixedResources.model_json_schema(),
#                 constraints=Constraints.model_json_schema(),
#                 phaseGeneration=PhaseGeneration.model_json_schema(),
#                 dailiesGeneration=DailiesGeneration.model_json_schema(),
#             ),
#             "response_mime_type": "application/json",
#             "response_schema": responseSchema,
#         },
#     )

def get_llm_response(session: ChatSession, user_input: str, db: Session=Depends(get_db)):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    current_phase = session.phase_tag
    
    if current_phase == "define_goal":
        response_schema = FollowUp | DefinitionsCreate
        prompt_template = PHASE_INSTRUCTIONS["define_goal"]
        format_args = {
            "followUp": FollowUp.model_json_schema(),
            "definitionsCreate": DefinitionsCreate.model_json_schema()
        }

    elif current_phase == "get_prerequisites":
        response_schema = FollowUp | GoalPrerequisites
        prompt_template = PHASE_INSTRUCTIONS["get_prerequisites"]
        format_args = {
            "goal_context": session.goal_obj,
            "followUp": FollowUp.model_json_schema(),
            "goalPrerequisites": GoalPrerequisites.model_json_schema()
        }

    elif current_phase in ["generate_phases", "refine_phases"]:
        response_schema = PhaseGeneration
        prompt_template = PHASE_INSTRUCTIONS[current_phase]
        format_args = {
            "goal_context": session.goal_obj,
            "prereq_context": session.prereq_obj,
            "phaseGeneration": PhaseGeneration.model_json_schema()
        }
    
    else:
        raise ValueError(f"Unknown phase: {current_phase}")

    DATE_FORMAT = '%Y-%m-%d'
    current_date_str = date.today().strftime(DATE_FORMAT)
    full_system_instruction = BASE_INSTRUCTION.format(current_date_str=current_date_str) + \
                              prompt_template.format(**format_args)

    chat_history = pickle.loads(session.session_data)
    new_user_message = Content(
        parts=[Part.from_text(text=user_input)],
        role='user'
    )
    chat_history.append(new_user_message)

    return client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=chat_history,
        config={
            "system_instruction": full_system_instruction,
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )

def generate_dailies(session: ChatSession, phase: PhaseCreate, db: Session=Depends(get_db)):

    all_phases_dailies = []
    if session.dailies_obj:
        all_phases_dailies = DailiesPost.model_validate_json(session.dailies_obj).dailies
        
    current_planning_date = phase.start_date

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

        valid_new_tasks = [t for t in new_tasks if t.dailies_date <= phase.end_date]
        all_phases_dailies.extend(valid_new_tasks)
        if valid_new_tasks != []:
            last_task_date = max(t.dailies_date for t in valid_new_tasks)
            current_planning_date = last_task_date + datetime.timedelta(days=1)
        else:
            current_planning_date += datetime.timedelta(days=14)
    
    return DailiesGeneration(status="dailies_generated", dailies=all_phases_dailies)

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

