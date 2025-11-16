import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

class ChatHistoryBase(BaseModel):
    text_num: int = Field(..., ge=1)
    role: str = Field(..., pattern="^(user|model)$")
    content: str

class ChatHistoryCreate(ChatHistoryBase):
    session_id: int

class ChatHistoryRead(ChatHistoryBase):
    id: int
    session_id: int

    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    current_phase: int = Field(..., ge=1)
    goal_id: Optional[int] = None 

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionRead(ChatSessionBase):
    session_id: int
    created_at: datetime
    
    history: List[ChatHistoryRead] = Field(default_factory=list)
    
    class Config:
        from_attributes = True