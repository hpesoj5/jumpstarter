from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    metric = Column(Text, index=True, nullable=False)
    purpose = Column(Text, index=True, nullable=False)
    deadline = Column(Date, index=True, nullable=False)
    prerequisites = Column(Text, nullable=True, default="") # for testing only

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="goals")

    phases = relationship("Phase", back_populates="goal", cascade="all, delete-orphan")

class Phase(Base):
    __tablename__ = "phases"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    estimated_end_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False, index=True) 
    goal = relationship("Goal", back_populates="phases") 
    dailies = relationship("Daily", back_populates="phase", cascade="all, delete-orphan")

class Daily(Base):
    __tablename__ = "dailies"
    id = Column(Integer, primary_key=True, index=True)
    task_description = Column(String, nullable=False)
    estimated_time_minutes = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=False, index=True) 
    phase = relationship("Phase", back_populates="dailies")