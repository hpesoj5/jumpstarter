from pydantic import BaseModel, Field
from typing import Literal
from backend.schemas.goal import DefinitionsCreate, GoalPrerequisites, PhaseGeneration, DailiesGeneration

# for clarifications from LLM
class FollowUp(BaseModel):
    status: Literal['follow_up_required'] = 'follow_up_required'
    question_to_user: str = Field(description="A single, specific, question to the user.")
    
# for FastAPI to return
class APIResponse(BaseModel):
    session_id: str
    data: FollowUp | DefinitionsCreate | GoalPrerequisites | PhaseGeneration | DailiesGeneration  # more specific phase-related models will be added

# --- Request Model ---
class APIRequest(BaseModel):
    user_input: str
    session_id: str | None = None
    phase: str
    
    '{\n  "status": "prerequisites_extracted",\n  "skill_level": "expert with 1800 rating",\n  "related_experience": [],\n  "resources_available": [\n    "Codeforces",\n    "AtCoder",\n    "local judge codebreaker.xyz"\n  ],\n  "user_gap_assessment": [],\n  "possible_gap_assessment": [\n    "Need to identify specific training areas for algorithms and data structures to bridge the gap from 1800 to 2100 rating.",\n    "May benefit from structured problem-solving strategies and contest simulation practice."\n  ],\n  "time_commitment_per_week_hours": 5,\n  "budget": 0,\n  "required_equipment": [\n    "computer",\n    "stable internet connection"\n  ],\n  "support_system": [\n    "friends doing CP"\n  ],\n  "blocked_time_blocks": [],\n  "available_time_blocks": []\n}'