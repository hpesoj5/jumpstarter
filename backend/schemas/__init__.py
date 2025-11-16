"""
This is how the user will interact with the database
"""
from .goal import GoalRequest,FollowUp,CurrentState,FixedResources,Constraints,GoalPrerequisites,DefinitionsBase,DefinitionsCreate,Definitions,PhaseBase,PhaseCreate,PhaseGeneration,PhaseRead,DailyTaskBase,DailyTaskCreate,DailyTaskGeneration,PhaseDailies,APIResponse,GoalConfirm
from .user import User, UserCreate, UserBase, UserLogin
