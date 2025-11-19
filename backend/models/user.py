from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    session_id = Column(Integer, ForeignKey("sessions.id"), index=True, nullable=True)
    session = relationship("Session", back_populates="user")
    goals = relationship("Goal", back_populates="owner")
