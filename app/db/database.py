import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models - update to use newer approach
# Base = declarative_base()  # Old way
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized")
    
    # Test connection with proper text() wrapper
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                print("Database connection test successful!")
            else:
                print("Database connection test returned unexpected result")
    except Exception as e:
        print(f"Connection error: {str(e)}")

if __name__ == "__main__":
    init_db()

def test_connection():
    db = next(get_db())
    try:
        # Execute a simple query
        result = db.execute("SELECT *").fetchone()
        if result[0] == 1:
            print("Database connection successful!")
        else:
            print("Something went wrong")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_connection()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    doc_id = Column(String, unique=True, index=True)
    content_type = Column(String)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    node_metadata = Column(Text, nullable=True) 