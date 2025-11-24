from sqlalchemy import Column, Integer, LargeBinary, String, CheckConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from backend.db.session import Base

phase_tag_list =  ["define_goal", "get_prerequisites", "generate_phases", "refine_phases", "generate_dailies"]
          
class ChatSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_data = Column(LargeBinary, nullable=False) # pickled chat object
    phase_tag = Column(String, default="define_goal", nullable=False)
    
    goal_obj = Column(JSON, nullable=True, default=None) # note on json: has to be python dict, if not, need to store as string
    prereq_obj = Column(JSON, nullable=True, default=None)
    phases_obj = Column(JSON, nullable=True, default=None)
    dailies_obj = Column(JSON, nullable=True, default=None)

    user = relationship("User", back_populates="session")

    __table_args__ = (
        CheckConstraint(phase_tag.in_(phase_tag_list), name="check_phase_tag"),
    )