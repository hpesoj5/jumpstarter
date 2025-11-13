from pydantic import BaseModel, Field
from typing import Union, List, Literal, Any
from datetime import date

# for clarifications from LLM
class FollowUp(BaseModel):
    status: Literal['follow_up_required'] = 'follow_up_required'
    question_to_user: str = Field(description="A single, specific, question to the user.")

# for FastAPI to return
class APIResponse(BaseModel):
    session_id: str
    data: Union[FollowUp, Any] # 'Any' will be replaced by specific phase-related models

# --- Request Model ---
class GoalRequest(BaseModel):
    user_input: str
    session_id: Union[str, None]

class DefinitionsBase(BaseModel):
    status: Literal['definitions_extracted'] = 'definitions_extracted'
    title: str = Field(description="The specific goal to achieve")
    metric: str = Field(description="The objective, quantifiable metric.")
    purpose: str = Field(description="The underlying motivation or 'why'.")
    deadline: date = Field(description="The date the goal must be completed by, formatted as YYYY-MM-DD.")
    
class DefinitionsCreate(DefinitionsBase):
    pass
    
class Definitions(DefinitionsBase):
    id: int
    prerequisites: str # Includes the data expected from Phase 2
    
    class Config:
        from_attributes = True 

class PhaseBase(BaseModel):
    title: str
    description: str
    estimated_end_date: date

class PhaseCreate(PhaseBase):
    pass # Used for POST request body

class PhaseRead(PhaseBase):
    id: int
    goal_id: int
    is_completed: bool

    class Config:
        from_attributes = True

class DailyBase(BaseModel):
    task_description: str
    estimated_time_minutes: int

class DailyCreate(DailyBase):
    pass # Used for POST request body

class DailyRead(DailyBase):
    id: int
    phase_id: int
    is_completed: bool

    class Config:
        from_attributes = True