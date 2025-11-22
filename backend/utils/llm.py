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
responseSchema = schemas.FollowUp | schemas.DefinitionsCreate | schemas.GoalPrerequisites | schemas.PhaseGeneration | schemas.DailiesGeneration

def get_session_id(api_request: schemas.APIRequest, chat_sessions: dict) -> tuple[bool, str]:
    if api_request.session_id and api_request.session_id in chat_sessions:
        return (True, api_request.session_id)
    elif api_request.session_id:
        return (False, api_request.session_id)
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
        
    elif api_request.phase == "define_goal": # the user has not chatted with the bot before
        chat = client.chats.create(
            model=model,
            config={
                "system_instruction": SYSTEM_INSTRUCTION.format(
                    followUp=schemas.FollowUp.model_json_schema(),
                    definitionsCreate=schemas.DefinitionsCreate.model_json_schema(),
                    goalPrerequisites=schemas.GoalPrerequisites.model_json_schema(),
                    phaseGeneration=schemas.PhaseGeneration.model_json_schema(),
                    dailiesGeneration=schemas.DailiesGeneration.model_json_schema(),
                ),
                "response_mime_type": "application/json",
                "response_schema": responseSchema,
            },
        )
        chat_sessions[session_id] = chat
        
    else:
        raise HTTPException(status_code=500, detail="LLM API Error: chat with LLM does not exist")
    
    try:
        current_date_str = date.today().strftime(DATE_FORMAT)
        message = f'CURRENT_PHASE = "{api_request.phase}"\ncurrent_date = {current_date_str}\n{api_request.user_input}'
        response = chat.send_message(message)
        results = response.parsed
        chat_sessions[session_id] = chat
        return schemas.APIResponse(session_id=session_id, data=results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API Error: {e}")
    
test_user = client.chats.create(
    model=model,
    config={
        "system_instruction": "You are a human user who is testing a goal-planning chatbot. You want to learn Japanese. Answer the questions given to you accordingly, in a human way (i.e. minimal formatting, direct, concise answers)"
    },
)
import time
tests_dir = backend_dir.parent / "tests"
def send_message(message: str, file, delay: int) -> str:
    time.sleep(delay)
    response = test_user.send_message(message).text
    print(f"USER: {response}")
    file.write(f"USER: {response}\n\n")
    return response

def main(): # to test the ability of the LLM to have a chat with the user resulting in PHASE GENERATION
    chat_sessions = {} 
    
    # DEFINING THE GOAL
    api_request = schemas.APIRequest(user_input="", phase="define_goal")
    session_id = get_session_id(api_request, chat_sessions)[1]
    
    # OPEN AND WRITE TO FILE
    with open(tests_dir / f"{session_id}.txt", 'w', encoding='utf-8') as chatlog_file:
        print("MODEL: What do you want to achieve?\nI want to:")
        chatlog_file.write("MODEL: What do you want to achieve?\nI want to:\n\n")
        api_request.user_input = f'I want to {send_message("I want to: ", chatlog_file, 2)}'
        api_response = query(api_request, chat_sessions)
        
        while api_response.data.status == "follow_up_required":
            print(f"MODEL: {api_response.data.question_to_user}")
            chatlog_file.write(f"MODEL: {api_response.data.question_to_user}\n\n")
            api_request.user_input = send_message(f"{api_response.data.question_to_user}", chatlog_file, 5)
            api_response = query(api_request, chat_sessions)

        goal = api_response.data
        if not isinstance(goal, schemas.DefinitionsCreate):
            print(f"LLM returned an unexpected format. Expected schemas.DefinitionsCreate, got {type(goal)}")
            return
        print(f"MODEL: {goal.model_dump()}")
        chatlog_file.write(f"MODEL: {goal.model_dump()}\n\n")

        # GETTING USER PREREQUISITES
        api_request.phase = "get_prerequisites"
        api_request.user_input = f'My goal is {goal.model_dump()}\nWhat prerequisites do you need from me?'
        api_response = query(api_request, chat_sessions)
        
        while api_response.data.status == "follow_up_required":
            print(f"MODEL: {api_response.data.question_to_user}")
            chatlog_file.write(f"MODEL: {api_response.data.question_to_user}\n\n")
            api_request.user_input = send_message(f"{api_response.data.question_to_user}", chatlog_file, 10)
            api_response = query(api_request, chat_sessions)
        
        prerequisites = api_response.data    
        if not isinstance(prerequisites, schemas.GoalPrerequisites):
            print(f"LLM returned an unexpected format. Expected schemas.DefinitionsCreate, got {type(prerequisites)}")
            return
        
        print(f"MODEL: {prerequisites.model_dump()}")
        chatlog_file.write(f"MODEL: {prerequisites.model_dump()}\n\n")
        
        # GENERATING PLAN PHASES
        api_request.phase = "generate_phases"
        api_request.user_input = f'My goal is {goal.model_dump()}\nMy prerequisites are {prerequisites.model_dump()}\nWhat should the plan look like?'
        api_response = query(api_request, chat_sessions)
        
        phases = api_response.data
        if not isinstance(phases, schemas.PhaseGeneration):
            print(f"LLM returned an unexpected format. Expected schemas.PhaseGeneration, got {type(phases)}")
            return
        
        print(f"MODEL: {phases.model_dump()}")
        chatlog_file.write(f"MODEL: {phases.model_dump()}\n\n")
        # SKIP PHASE REFINING FOR NOW
        
        # GENERATING DAILY TASKS
        api_request.phase = "generate_dailies"
        start_date = date.today().strftime(DATE_FORMAT)
        api_request.user_input = f'My goal is {goal.model_dump()}\nMy prerequisites are {prerequisites.model_dump()}\nThe overall plan is {phases.model_dump()}\nThe current phase is 1\nCan you generate a daily schedule for me starting from {start_date}?'
        api_response = query(api_request, chat_sessions)
        
        dailies = api_response.data
        if not isinstance(dailies, schemas.DailiesGeneration):
            print(f"LLM returned an unexpected format. Excepted schemas.DailiesGeneration, got {type(dailies)}")
        
        print(f"MODEL: {dailies.model_dump()}")
        chatlog_file.write(f"MODEL: {dailies.model_dump()}\n\n")
    
if __name__ == "__main__":
    main()