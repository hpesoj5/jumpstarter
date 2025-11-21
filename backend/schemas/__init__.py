"""
This is how the user will interact with the database
"""
from .api import FollowUp, APIResponse, APIRequest
from .goal import DefinitionsBase, DefinitionsCreate, Definitions, CurrentState, FixedResources, Constraints, GoalPrerequisites, PhaseGeneration, PhaseCreate, DailiesGeneration
from .user import User, UserCreate, UserBase, UserLogin