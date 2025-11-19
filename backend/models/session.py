from sqlalchemy import Column, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_data = Column(LargeBinary, nullable=False) # pickled chat object
    goal_obj = Column(JSON, nullable=True) # note on json: has to be python dict, if not, need to store as string
    phases_obj = Column(JSON, nullable=True)

    user = relationship("User", back_populates="session")