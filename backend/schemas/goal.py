from pydantic import BaseModel, Field
from typing import List, Literal, Any
from datetime import date

# for clarifications from LLM
class FollowUp(BaseModel):
    status: Literal['follow_up_required'] = 'follow_up_required'
    question_to_user: str = Field(description="A single, specific, question to the user.")

# for FastAPI to return
class APIResponse(BaseModel):
    session_id: str
    data: Any # 'Any' will be replaced by specific phase-related models

# --- Request Model ---
class APIRequest(BaseModel):
    user_input: str
    session_id: str | None = None

class DefinitionsBase(BaseModel):
    status: Literal['definitions_extracted'] = 'definitions_extracted'
    title: str = Field(description="The specific goal to achieve")
    metric: str = Field(description="The objective, quantifiable metric.")
    purpose: str = Field(description="The underlying motivation or 'why'.")
    deadline: date = Field(description="The date the goal must be completed by, formatted as YYYY-MM-DD.")
    
class DefinitionsCreate(DefinitionsBase):
    status: Literal['definitions_extracted'] = 'definitions_extracted'
    # are you doing something with this, judging from your other create schemas
    
class Definitions(DefinitionsBase):
    id: int
    prerequisites: str # Includes the data expected from Phase 2
    
    class Config:
        from_attributes = True

class CurrentState(BaseModel):
    """Details about the user's starting point and gaps."""
    skill_level: str = Field(description="The user's current skill level related to the goal.")
    related_experience: str = Field(description="Relevant past experience or projects.")
    resources_available: str = Field(description="Current readily available resources (tools, software, people).")
    user_gap_assessment: List[str] = Field(description="A list of problems or missing skills the user has identified.")
    possible_gap_assessment: List[str] = Field(description="A list of problems or missing skills identified by the LLM (optional, for planning assistance).")

class FixedResources(BaseModel):
    """Non-negotiable resource constraints."""
    time_commitment_per_week_hours: float = Field(description="The number of hours the user can reliably commit per week.")
    budget: float = Field(description="The monetary budget available for the goal (in the user's local currency, e.g., 'USD').")
    required_equipment: str = Field(description="Specific equipment or materials needed to start or complete the goal.")
    support_system: str = Field(description="People or groups available for emotional or practical support.")

class Constraints(BaseModel):
    """Scheduling and external limitations."""
    blocked_time_blocks: List[str] = Field(description="Specific recurring time blocks (e.g., 'Mondays 9am-5pm') when the user is unavailable.")
    available_time_blocks: List[str] = Field(description="Specific recurring time blocks (e.g., 'Tuesday 7pm-9pm') when the user is free to work on the goal.")
    dependencies: List[str] = Field(description="A list of external requirements that must be met before the goal can progress (e.g., 'Wait for equipment delivery').")

class GoalPrerequisites(CurrentState, FixedResources, Constraints):
    """The complete structure for all prerequisites."""
    status: Literal['prerequisites_extracted'] = 'prerequisites_extracted'

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
    estimated_time_minutes: int

class DailyCreate(DailyBase):
    pass # Used for POST request body

class DailyRead(DailyBase):
    id: int
    phase_id: int
    is_completed: bool

    class Config:
        from_attributes = True