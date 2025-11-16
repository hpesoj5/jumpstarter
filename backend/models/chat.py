import uuid
from sqlalchemy import Column, Integer, UniqueConstraint, CheckConstraint, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.session import Base

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    session_id = Column(Integer, primary_key=True, index=True)
    
    current_phase = Column(Integer, nullable=False, default=1)
    
    goal_id = Column(Integer, ForeignKey('goals.id', ondelete='SET NULL'), nullable=True)
    goal = relationship("Goal")

    history = relationship(
        "ChatHistory", 
        back_populates="session", 
        cascade="all, delete-orphan", # 'cascade' ensures messages are deleted when the session is.
        order_by="ChatHistory.text_num" # Order by text_num (the message sequence number)
    )

class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True, index=True)
    
    session_id = Column(Integer,
        ForeignKey('chat_sessions.session_id', ondelete='CASCADE'), 
        nullable=False
    )
    
    text_num = Column(Integer, nullable=False) # track message order
    role = Column(String(50), nullable=False) # Role: 'user' or 'model'
    content = Column(Text, nullable=False) 

    __table_args__ = (
        UniqueConstraint('session_id', 'text_num', name='_session_text_uc'), # composite key
        CheckConstraint(role.in_(['prompt', 'user', 'model']), name='role_check')
    )

    session = relationship("ChatSession", back_populates="history")