import logging
import os
import atexit
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.endpoints import papers, queries
from app.core.config import settings
from app.db.database import init_db
from app.api.endpoints.queries import initialize_index
from app.rag.redis_manager import RedisManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Global Redis manager instance
redis_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_manager
    
    # Initialize Redis
    redis_manager = RedisManager()
    
    # Only initialize if not already initialized
    if not redis_manager.is_initialized():
        # Initialize database
        init_db()
        
        # Initialize index
        try:
            await initialize_index()
            logging.info("System initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing system: {str(e)}")
    else:
        logging.info("Using existing system state from Redis")
    
    yield
    
    # Cleanup on shutdown
    if redis_manager:
        try:
            redis_manager.cleanup()
            logging.info("Cleaned up Redis resources")
        except Exception as e:
            logging.error(f"Error during Redis cleanup: {str(e)}")

# Register cleanup function with atexit
atexit.register(lambda: redis_manager.cleanup() if redis_manager else None)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(papers.router, prefix=f"{settings.API_V1_STR}/papers", tags=["papers"])
app.include_router(queries.router, prefix=f"{settings.API_V1_STR}/queries", tags=["queries"])

@app.get("/")
async def root():
    return {"message": "Welcome to the RAG Research Paper Assistant API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 