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

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=GOOGLE_API_KEY)
DATE_FORMAT = '%Y-%m-%d'
model = 'gemini-2.5-flash-lite'

def get_session_id(api_request: schemas.APIRequest, chat_sessions: dict):
    if api_request.session_id and api_request.session_id in chat_sessions:
        return (True, api_request.session_id)
    else:
        api_request.session_id = str(uuid.uuid4())
        return (False, api_request.session_id)

def define_goal(api_request: schemas.APIRequest, chat_sessions: dict):
    """
    Returns goal with the four fields: 'goal', 'metric', 'purpose' and 'deadline', or a follow up question.
    Also updates chat_sessions.
    """
    # Session exists; follow up with questions
    chat_exists, session_id = get_session_id(api_request, chat_sessions)
    if chat_exists:
        chat: Chat = chat_sessions[session_id]
    else:
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
                "response_schema": schemas.FollowUp | schemas.DefinitionsCreate | schemas.GoalPrerequisites,
            },
        )
        chat_sessions[session_id] = chat
        
    # user interaction with Gemini API
    try:
        response = chat.send_message(api_request.user_input)
        results = response.parsed
        chat_sessions[session_id] = chat
        print(results)
        return schemas.APIResponse(session_id=session_id, data=results) # should modify chat_sessions in place as well
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")
    
def get_prerequisites(api_request: schemas.APIRequest, chat_sessions: dict):
    """
    Returns the goal prerequisites, or a follow up question.
    Also updates chat_sessions.
    """
    
    chat_exists, session_id = get_session_id(api_request, chat_sessions)
    if chat_exists:
        chat: Chat = chat_sessions[session_id]
    else:
        raise HTTPException(status_code=500, detail="LLM API Error: chat with LLM does not exist")
        
    try:
        response = chat.send_message(api_request.user_input)
        results = response.parsed
        chat_sessions[session_id] = chat
        print(results)
        return schemas.APIResponse(session_id=session_id, data=results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")
    
# def generate_phases(api_request: schemas.APIRequest, goal: schemas.Definitions, phases: dict, chat_sessions: dict):
#     """
#     Using the defined goal and prerequisites, returns the phases in the realistic, sequential plan
#     """
    
#     chat_exists, session_id = get_session_id(api_request, chat_sessions)
    
#     if chat_exists:
#         chat = chat_sessions[session_id]
#     else:
#         current_date_str = date.today().strftime(DATE_FORMAT)
#         chat = client.models.create(
#             model=model,
#             config={
#                 "system_instruction": PHASE_GENERATION_INSTRUCTION.format(
#                     goal=goal,
#                     current_date_str=current_date_str,
#                     phaseGeneration=schemas.PhaseGeneration.model_json_schema(),
#                 ),
#                 "response_mime_type": "application/json",
#                 "response_schema": schemas.PhaseGeneration,
#             },
#         )
#         chat_sessions[session_id] = chat
        
#     try:
#         response = chat.send_message("What should the plan look like?")
#         results = response.parsed
#         chat_sessions[session_id] = chat
#         return schemas.APIResponse(session_id, data=results)
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")
    
# def refine_phases(api_request: schemas.APIRequest, goal: schemas.Definitions, phases: schemas.PhaseCreate, chat_sessions: dict):
    
#     chat_exists, session_id = get_session_id(api_request, chat_sessions)
    
#     if chat_exists:
#         chat = chat_sessions[session_id]
#     else:
#         current_date_str = date.today().strftime(DATE_FORMAT)
#         chat = client.chats.create(
#             model=model,
#             config={
#                 "system_instruction": PHASE_REFINEMENT_INSTRUCTION.format(
#                     goal=goal,
#                     current_date_str=current_date_str,
#                     phaseGeneration=schemas.PhaseGeneration,
#                     phases=phases,
#                 ),
#                 "response_mime_type": "application/json",
#                 "response_schema": schemas.PhaseGeneration,
#             },
#         )
#         chat_sessions[session_id] = chat
            
#     try:
#         response = chat.send_message(api_request.user_input)
#         results = response.parsed
#         chat_sessions[session_id] = chat
#         return schemas.APIResponse(session_id, data=results)
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")
    
# # def generate_dailies(api_request: schemas.APIRequest, goal: schemas.Definitions, phases: schemas.PhaseCreate, chat_sessions: dict)
        
def main():
    chat_sessions = {}
    # testing definition creation
    
    print("What do you want to do?")
    user_input = input("I want to: ")
    parsed_input = 'CURRENT_PHASE = "define_goal"\nI want to: ' + user_input
    user_request = schemas.APIRequest(user_input=parsed_input, session_id=None)
    apiresponse = define_goal(user_request, chat_sessions)
    session_id = apiresponse.session_id
    while apiresponse.data.status == "follow_up_required":
        user_input = input(apiresponse.data.question_to_user)
        parsed_input = f'CURRENT_PHASE = "define_goal"\n{user_input}'
        api_request = schemas.APIRequest(user_input=parsed_input, session_id=session_id)
        apiresponse = define_goal(api_request, chat_sessions)

    response = apiresponse.data
    
    if not isinstance(response, schemas.DefinitionsCreate):
        print(f"LLM returned an unexpected format. Expected schemas.DefinitionsCreate, got {type(response)}")
        return
        
    print(f"Goal: {response.title}")
    print(f"Metric: {response.metric}")
    print(f"Purpose: {response.purpose}")
    print(f"Deadline: {response.deadline}")
    
    goal = response
    parsed_input = f"""
    CURRENT_PHASE: "get_prerequisites"
    My goal is {goal.model_json_schema()}
    What prerequisites do you need from me?
    """
    user_request = schemas.APIRequest(user_input=parsed_input, session_id=session_id)
    apiresponse = get_prerequisites(user_request, chat_sessions)
    while apiresponse.data.status == "follow_up_required":
        user_input = input(apiresponse.data.question_to_user)
        parsed_input = f'CURRENT_PHASE = "get_prerequisites"\n{user_input}'
        user_request = schemas.APIRequest(user_input=parsed_input, session_id=session_id)
        apiresponse = get_prerequisites(user_request, chat_sessions)
        
    response = apiresponse.data
        
    if not isinstance(response, schemas.GoalPrerequisites):
        print(f"LLM returned an unexpected format. Expected schemas.DefinitionsCreate, got {type(response)}")
        return
    
    print(response)
    
if __name__ == "__main__":
    main()