from typing import Any
from pydantic import BaseModel, Json

class SessionBase(BaseModel):
    session_data: bytes

class Session(SessionBase):
    id: int
    goal_obj = Json[Any]
    prereq_obj = Json[Any]
    phases_obj = Json[Any]
    class Config:
        from_attributes = True
