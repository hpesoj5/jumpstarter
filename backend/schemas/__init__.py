"""
This is how the user will interact with the database
"""
from .api import FollowUp, GoalCompleted, APIResponse, APIRequest, ConfirmRequest
from .goal import DefinitionsBase, DefinitionsCreate, Definitions, GoalPrerequisites, PhaseGeneration, PhaseCreate, DailiesGeneration, DailiesPost, DailyRead, DailiesRequest, DailiesResponse, UpdateRequest, GoalProgressRead, TitleRequest, PhaseResponse
from .user import User, UserCreate, UserBase, UserLogin
