from pydantic import BaseModel, Field
from typing import Literal, Union
from backend.schemas.goal import DefinitionsCreate, GoalPrerequisites, PhaseGeneration, DailiesGeneration, DailiesPost

# possibly add response models here
class FollowUp(BaseModel):
    status: Literal['follow_up_required'] = 'follow_up_required'
    question_to_user: str = Field(description="A single, specific, question to the user.")

class APIResponse(BaseModel):
    phase_tag: Literal["define_goal", "get_prerequisites", "refine_phases", "generate_dailies"]
    ret_obj: Union[FollowUp , DefinitionsCreate , GoalPrerequisites , PhaseGeneration , DailiesPost]

class APIRequest(BaseModel):
    user_input: str

class ConfirmRequest(BaseModel):
    confirm_obj: DefinitionsCreate | GoalPrerequisites | PhaseGeneration | DailiesPost # goal prereq only used by backend to transition