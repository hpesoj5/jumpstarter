from pydantic import BaseModel

class GoalBase(BaseModel):
    title: str
    description: str | None = None

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True
