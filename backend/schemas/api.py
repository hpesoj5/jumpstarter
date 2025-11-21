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