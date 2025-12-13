"""
This is how the user will interact with the database
"""
from .api import FollowUp, GoalCompleted, APIResponse, APIRequest, ConfirmRequest
from .goal import DefinitionsBase, DefinitionsCreate, Definitions, CurrentState, FixedResources, Constraints, GoalPrerequisites, PhaseGeneration, PhaseCreate, DailiesGeneration, DailiesPost, DailyRead, DailyIdsList, GoalProgressRead
from .user import User, UserCreate, UserBase, UserLogin
