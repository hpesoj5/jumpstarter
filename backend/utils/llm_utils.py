import datetime, pickle, json, re
from datetime import date

from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from backend.models import ChatSession
from backend.schemas import (FollowUp,
                            DefinitionsCreate, 
                            CurrentState, FixedResources, Constraints, GoalPrerequisites, 
                            PhaseGeneration, PhaseCreate,
                            DailiesGeneration, DailiesPost,)
#from backend.utils.system_instruction import SYSTEM_INSTRUCTION, DAILIES_GENERATION_PROMPT
from backend.utils.instruction_chain import BASE_INSTRUCTION, PHASE_INSTRUCTIONS, SEARCH_INSTRUCTION, DAILIES_GENERATION_INSTRUCTION

from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam

from google import genai
from google.genai.types import Content, Part, Tool, GoogleSearch

import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPEN_API_KEY = os.getenv("OPEN_API_KEY")

GEMINI_MODEL = os.getenv("GEMINI_MODEL")
OPEN_MODEL = os.getenv("OPEN_MODEL")

openrouter_client = OpenAI(
    api_key=OPEN_API_KEY, 
    base_url="https://openrouter.ai/api/v1",
)
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

def get_llm_response(session: ChatSession, user_input: str, db):
    
    current_phase = session.phase_tag
    
    if current_phase == "define_goal":
        response_schema = FollowUp | GoalPrerequisites
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
    chat_history.append({"role": "user", "content": user_input})

    response = openrouter_client.responses.parse(
        model=OPEN_MODEL,
        input=[
            {"role": "system", "content": full_system_instruction},
            *chat_history,
        ],
        text_format=response_schema,
    )
    return response

def fetch_phase_resources(session: ChatSession, phase: PhaseCreate):
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=SEARCH_INSTRUCTION.format(
            goal_json=session.goal_obj,
            prereq_json=session.prereq_obj,
            phases_json=session.phases_obj,
            phase_title=phase.title
        ),
        config={
            "tools": [Tool(google_search=GoogleSearch())],
            "response_mime_type": "text/plain", # only mode allowed
            "temperature": 1.2
        },
    )
    
    # Extract text safely
    try:
        resource_links = {i: chunk.web.uri for i, chunk in enumerate(response.candidates[0].grounding_metadata.grounding_chunks)}
        reference_text_map = {}
        lines = response.text.split("\n")
        for resource in response.candidates[0].grounding_metadata.grounding_supports:
            for line in lines:
                if resource.segment.text in line:
                    
                    full_text = f"{line}".strip()
                    
                    reference_text_map[tuple(resource.grounding_chunk_indices)] = full_text
        return resource_links, reference_text_map
    except Exception as e:
        return {}, {}
    
def generate_dailies(session: ChatSession, phase: PhaseCreate, db):

    all_phases_dailies = []
    if session.dailies_obj:
        all_phases_dailies = DailiesPost.model_validate_json(session.dailies_obj).dailies
        
    current_planning_date = phase.start_date
    resource_links, reference_text_map = fetch_phase_resources(session, phase)
    resource = "\n".join(f"{k}: {reference_text_map[k]}" for k in reference_text_map)

    while current_planning_date <= phase.end_date:
        if current_planning_date > phase.end_date:
                break
        
        dailies_generation_prompt = f"""
                                        The currently confirmed tasks for this goal (for context and continuity) is: {all_phases_dailies}.
                                        Generate the daily schedule for the next 2 weeks starting from, and including {current_planning_date}
                                        """

        response = openrouter_client.responses.parse(
            model=OPEN_MODEL,
            input=[
                {
                    "role": "system",
                    "content": DAILIES_GENERATION_INSTRUCTION.format(
                        dailiesGeneration=DailiesGeneration.model_json_schema(),
                        phase_resources=resource,
                        goal_obj=session.goal_obj,
                        prereq_obj=session.prereq_obj,
                        phases_obj=session.phases_obj,
                        phase_title=phase.title,
                    ),
                },
                {
                    "role": "user",
                    "content": f"{dailies_generation_prompt}",
                },
                
            ],
            text_format=DailiesGeneration,
        )
        
        response = parse_response(response)
        new_tasks = response.dailies

        valid_new_tasks = [t for t in new_tasks if t.dailies_date <= phase.end_date]

        for daily in valid_new_tasks:
            match = re.search(r'\s*\((\d+(?:,\s*\d+)*)\)\s*$', daily.task_description)
            if match:
                ref_str = match.group(1)
                citation_markers_to_remove = match.group(0)
                references = tuple(map(int, ref_str.split(',')))
                daily.task_description = daily.task_description.replace(citation_markers_to_remove, '').strip()
                
                daily.task_description += "\n Resources: (Please copy and paste)"
                for reference in references:
                    if reference in resource_links:
                        daily.task_description += f"\n[{reference+1}] {resource_links[reference]}\n"
            daily.task_description = re.sub(r'\(([^)]*)\)\s*$', '', daily.task_description).strip()

        all_phases_dailies.extend(valid_new_tasks)
        if valid_new_tasks != []:
            last_task_date = max(t.dailies_date for t in valid_new_tasks)
            current_planning_date = last_task_date + datetime.timedelta(days=1)
        else:
            current_planning_date += datetime.timedelta(days=14)
    
    return DailiesGeneration(status="dailies_generated", dailies=all_phases_dailies)

def parse_response(response): # can do more parsing but thats kinda a lot of work i.e. check for missing fields
    models = TypeAdapter(FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration | DailiesGeneration)
    text = response.output[1].content[0].text
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

