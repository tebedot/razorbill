from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False) # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(Text, nullable=False)
