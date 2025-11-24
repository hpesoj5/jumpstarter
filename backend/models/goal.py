from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Boolean, Float, Time
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    metric = Column(Text, index=True, nullable=False)
    purpose = Column(Text, index=True, nullable=False)
    deadline = Column(Date, index=True, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    owner = relationship("User", back_populates="goals")

    # Prerequisites, need to be unwraped to pass in
    skill_level = Column(Text)
    related_experience = Column(ARRAY(Text))
    resources_available = Column(ARRAY(Text))
    user_gap_assessment = Column(ARRAY(Text))
    possible_gap_assessment = Column(ARRAY(Text))

    time_commitment_per_week_hours = Column(Float)
    budget = Column(Float)
    required_equipment = Column(ARRAY(String))
    support_system = Column(ARRAY(String))

    blocked_time_blocks = Column(ARRAY(String))
    available_time_blocks = Column(ARRAY(String))

    phases = relationship("Phase", back_populates="goal", cascade="all, delete-orphan")

class Phase(Base):
    __tablename__ = "phases"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    estimated_end_date = Column(Date, nullable=False)
    is_completed = Column(Boolean, default=False)
    
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False, index=True) 
    goal = relationship("Goal", back_populates="phases") 
    dailies = relationship("Daily", back_populates="phase", cascade="all, delete-orphan")

class Daily(Base):
    __tablename__ = "dailies"
    id = Column(Integer, primary_key=True, index=True)
    task_description = Column(String, nullable=False)
    dailies_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    estimated_time_minutes = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=False, index=True) 
    phase = relationship("Phase", back_populates="dailies")