from fastapi import HTTPException
from google import genai
from google.genai.chats import Chat
import uuid
from datetime import date
from backend import schemas
from backend.utils.system_instruction import SYSTEM_INSTRUCTION

import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve()
load_dotenv("backend\\.env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)
DATE_FORMAT = '%Y-%m-%d'
model = 'gemini-2.5-flash-lite'
responseSchema = schemas.FollowUp | schemas.DefinitionsCreate | schemas.GoalPrerequisites | schemas.PhaseGeneration

def get_session_id(api_request: schemas.APIRequest, chat_sessions: dict) -> tuple[bool, str]:
    if api_request.session_id and api_request.session_id in chat_sessions:
        return (True, api_request.session_id)
    else:
        api_request.session_id = str(uuid.uuid4())
        return (False, api_request.session_id)

def query(api_request: schemas.APIRequest, chat_sessions: dict) -> schemas.APIResponse:
    """
    Sends a query to the LLM and returns the response schema.
    """
    chat_exists, session_id = get_session_id(api_request, chat_sessions)
    
    if chat_exists: # restore chat history
        chat: Chat = chat_sessions[session_id]
        print(chat.get_history())
        
    elif api_request.phase == "define_goal": # the user has not chatted with the bot before
        current_date_str = date.today().strftime(DATE_FORMAT)
        chat = client.chats.create(
            model=model,
            config={
                "system_instruction": SYSTEM_INSTRUCTION.format(
                    current_date_str=current_date_str,
                    followUp=schemas.FollowUp.model_json_schema(),
                    definitionsCreate=schemas.DefinitionsCreate.model_json_schema(),
                    goalPrerequisites=schemas.GoalPrerequisites.model_json_schema(),
                    currentState=schemas.CurrentState.model_json_schema(),
                    fixedResources=schemas.FixedResources.model_json_schema(),
                    constraints=schemas.Constraints.model_json_schema(),
                    phaseGeneration=schemas.PhaseGeneration.model_json_schema(),
                ),
                "response_mime_type": "application/json",
                "response_schema": responseSchema,
            },
        )
        chat_sessions[session_id] = chat
        
    else:
        raise HTTPException(status_code=500, detail="LLM API Error: chat with LLM does not exist")
    
    try:
        message = f'CURRENT_PHASE = "{api_request.phase}"\n{api_request.user_input}'
        response = chat.send_message(message)
        results = response.parsed
        chat_sessions[session_id] = chat
        return schemas.APIResponse(session_id=session_id, data=results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")

def main(): # to test the ability of the LLM to have a chat with the user resulting in PHASE GENERATION
    chat_sessions = {}
  
    # DEFINING THE GOAL
    print("What do you want to do?")
    user_input = f'I want to {input("I want to:\n")}'
    api_request = schemas.APIRequest(user_input=user_input, phase="define_goal")
    api_response = query(api_request, chat_sessions)
    
    while api_response.data.status == "follow_up_required":
        api_request.user_input = input(f"{api_response.data.question_to_user}\n")
        api_response = query(api_request, chat_sessions)

    goal = api_response.data
    if not isinstance(goal, schemas.DefinitionsCreate):
        print(f"LLM returned an unexpected format. Expected schemas.DefinitionsCreate, got {type(goal)}")
        return
    print(goal)
    print(goal.model_dump_json())

    # GETTING USER PREREQUISITES
    api_request.phase = "get_prerequisites"
    api_request.user_input = f'My goal is {goal.model_dump_json()}\nWhat prerequisites do you need from me?'
    api_response = query(api_request, chat_sessions)
    
    while api_response.data.status == "follow_up_required":
        api_request.user_input = input(f"{api_response.data.question_to_user}\n")
        api_response = query(api_request, chat_sessions)
    
    prerequisites = api_response.data    
    if not isinstance(prerequisites, schemas.GoalPrerequisites):
        print(f"LLM returned an unexpected format. Expected schemas.DefinitionsCreate, got {type(prerequisites)}")
        return
    print(prerequisites)
    print(prerequisites.model_dump_json())

    # GENERATING PLAN PHASES
    api_request.phase = "generate_phases"
    api_request.user_input = f'My goal is {goal.model_dump_json()}\nMy prerequisites are {prerequisites.model_dump_json()}\nWhat should the plan look like?'
    api_response = query(api_request, chat_sessions)
    
    phases = api_response.data
    if not isinstance(phases, schemas.PhaseGeneration):
        print(f"LLM returned an unexpected format. Expected schemas.PhaseGeneration, got {type(phases)}")
        return
    print(phases)
    print(phases.model_dump_json())
    
if __name__ == "__main__":
    main()