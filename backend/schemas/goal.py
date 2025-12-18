from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Any
from datetime import date, time
    
class DefinitionsBase(BaseModel):
    status: Literal['definitions_extracted'] = 'definitions_extracted'
    title: str = Field(description="The specific goal to achieve")
    metric: str = Field(description="The objective, quantifiable metric.")
    purpose: str = Field(description="The underlying motivation or 'why'.")
    deadline: date = Field(description="The date the goal must be completed by, formatted as YYYY-MM-DD.")
    
class DefinitionsCreate(DefinitionsBase):
    status: Literal['definitions_extracted'] = 'definitions_extracted'
    # are you doing something with this, judging from your other create schemas. just an identifier in case it is needed

class GoalPrerequisites(BaseModel):
    """The complete structure for all prerequisites."""
    status: Literal['prerequisites_extracted'] = 'prerequisites_extracted'
    related_experience: List[str] = Field(description="Relevant past experience or projects.", default=[])
    time_commitment_per_week_hours: float = Field(description="The number of hours the user can reliably commit per week.")
    blocked_time_blocks: List[str] = Field(description="Specific recurring time blocks (e.g., 'Mondays 9am-5pm') when the user is absolutely unavailable.", default=[])
    budget: float = Field(description="The monetary budget available for the goal (in the user's local currency, e.g., 'USD').", default=0.0)
    required_resources: List[str] = Field(description="Specific equipment or materials needed to start or complete the goal.", default=[])
    possible_gap_assessment: List[str] = Field(description="A list of problems or missing skills identified by the LLM (optional, for planning assistance).", default=[])

class Definitions(DefinitionsBase):
    id: int
    prerequisites: GoalPrerequisites # Includes the data expected from Phase 2
    
    class Config:
        from_attributes = True

class PhaseBase(BaseModel):
    title: str = Field(
        description="A descriptive title for the phase (e.g., 'Foundation Building', 'Skill Consolidation')."
    )
    description: str = Field(
        description="A detailed description of the phase's measurable target and objective (e.g., 'Run 10km under 60 minutes' or 'Complete chapters 1-5 and pass the unit test')."
    )
    start_date: date = Field(
        description="The estimated starting date for this phase, formatted as YYYY-MM-DD."
    )
    end_date: date = Field(
        description="The estimated completion date for this phase, formatted as YYYY-MM-DD. This date marks the achievement of the phase's target."
    )

class PhaseCreate(PhaseBase):
    pass # Used for POST request body

class PhaseGeneration(BaseModel):
    """Container for the variable list of generated phases."""
    status: Literal['phases_generated'] = 'phases_generated'
    phases: List[PhaseCreate] = Field(
        description="A list of 3 to 5 broad, sequential phases required to achieve the user's goal."
    )

class PhaseRead(PhaseBase):
    id: int
    goal_id: int
    is_completed: bool

    class Config:
        from_attributes = True

class DailyBase(BaseModel):
    task_description: str
    dailies_date: date
    start_time: time
    estimated_time_minutes: int
    phase_title: str

class DailyCreate(DailyBase):
    pass # Used for POST request body

class DailiesGeneration(BaseModel):
    """Container for the list of daily tasks for each phase"""
    status: Literal['dailies_generated'] = 'dailies_generated'
    dailies: List[DailyCreate] = Field(
        description="A list of specific, actionable and measurable daily tasks to achieve the phase."
    )

class DailyRead(DailyBase):
    id: int
    phase_id: int
    is_completed: bool

    class Config:
        from_attributes = True
        
    @model_validator(mode="before")
    def compute_phase_title(cls, data):
        if not isinstance(data, dict):
            obj = data
            data = {
                "id": obj.id,
                "dailies_date": obj.dailies_date,
                "estimated_time_minutes": obj.estimated_time_minutes,
                "is_completed": obj.is_completed,
                "phase_id": obj.phase_id,
                "phase_title": obj.phase.title,
                "start_time": obj.start_time,
                "task_description": obj.task_description,
            }
        
        return data
                
class DailiesPost(DailiesGeneration):
    goal_phases: List[str]
    curr_phase: str

class DailiesRequest(BaseModel):
    goal_id: int
    completed: bool
    
class PhaseResponse(BaseModel):
    goal_phases: List[str]
    
class DailiesResponse(BaseModel):
    dailies: List[DailyRead]

class UpdateRequest(BaseModel):
    ids: List[int]
    completed: bool

class GoalProgress(BaseModel):
    title: str
    total_dailies: int
    completed_dailies: int
    deadline: date

class GoalProgressRead(BaseModel):
    goals: List[GoalProgress]

class TitleRequest(BaseModel):
    goal_id: int | None
