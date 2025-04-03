import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.config import settings
from app.rag.redis_manager import RedisManager

logger = logging.getLogger(__name__)

# Create Redis manager
redis_manager = RedisManager()

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models - update to use newer approach
# Base = declarative_base()  # Old way
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

# Import models to ensure they are registered with Base
from app.db.models import Node

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database"""
    try:
        # Check if database is already initialized in Redis
        if redis_manager.redis_client.get("db_initialized"):
            return  # Silently return if already initialized

        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Test database connection
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        
        # Mark database as initialized in Redis
        redis_manager.redis_client.set("db_initialized", "true")
        logger.info("Database initialized")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()

def test_connection():
    db = next(get_db())
    try:
        # Execute a simple query
        result = db.execute(text("SELECT 1")).fetchone()
        if result[0] == 1:
            print("Database connection successful!")
        else:
            print("Something went wrong")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_connection() 