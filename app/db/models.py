from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True)
    node_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    node_metadata = Column(Text, nullable=True) 