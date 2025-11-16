from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Boolean, Float, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    is_planning_complete = Column(Boolean, nullable=False, default=False)
    
    title = Column(String(255), nullable=False)
    metric = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)
    deadline = Column(Date, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="goals")
    
    prerequisites = relationship("Prerequisite", back_populates="goal", uselist=False, cascade="all, delete-orphan")
    phases = relationship("Phase", back_populates="goal", cascade="all, delete-orphan")

class Prerequisite(Base):
    """Stores the complete Prerequisites data (Phase 2). One-to-one relationship with Goal."""
    __tablename__ = 'prerequisites'

    # Primary key is also the foreign key to ensure a 1:1 relationship
    goal_id = Column(Integer, ForeignKey('goals.id', ondelete='CASCADE'), primary_key=True)
    
    # CurrentState fields
    skill_level = Column(String(100), nullable=False)
    related_experience = Column(Text, nullable=False)
    resources_available = Column(Text, nullable=False)
    user_gap_assessment = Column(JSONB, nullable=False, default=[])  # List[str]
    possible_gap_assessment = Column(JSONB, nullable=False, default=[]) # List[str]

    # FixedResources fields
    time_commitment_per_week_hours = Column(Float, nullable=False)
    budget = Column(Float, nullable=False)
    required_equipment = Column(Text, nullable=False)
    support_system = Column(Text, nullable=False)

    # Constraints fields
    blocked_time_blocks = Column(JSONB, nullable=False, default=[]) # List[str]
    available_time_blocks = Column(JSONB, nullable=False, default=[]) # List[str]
    dependencies = Column(JSONB, nullable=False, default=[]) # List[str]
    
    goal = relationship("Goal", back_populates="prerequisites")

class Phase(Base):
    __tablename__ = 'phases'

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey('goals.id', ondelete='CASCADE'), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_completed = Column(Boolean, nullable=False, default=False) 
    
    goal = relationship("Goal", back_populates="phases")
    daily_tasks = relationship("DailyTask", back_populates="phase", cascade="all, delete-orphan")


class DailyTask(Base):
    __tablename__ = 'daily_tasks'

    id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey('phases.id', ondelete='CASCADE'), nullable=False)
    
    description = Column(Text, nullable=False)
    dailies_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    time_needed_minutes = Column(Integer, nullable=False)
    suggested_resource = Column(JSONB, nullable=False, default=[]) # List[str]
    is_completed = Column(Boolean, nullable=False, default=False)
    
    phase = relationship("Phase", back_populates="daily_tasks")