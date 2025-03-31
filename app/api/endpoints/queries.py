import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import pickle

from app.rag.index_manager import IndexManager
from app.rag.query_engine import QueryProcessor
from app.rag.document_processor import DocumentProcessor
from app.rag.redis_manager import RedisManager

router = APIRouter()
index_manager = IndexManager()
document_processor = DocumentProcessor()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str

class SourceNode(BaseModel):
    text: str
    score: Optional[float] = None
    doc_id: Optional[str] = None
    arxiv_url: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    source_nodes: List[SourceNode] = []

async def initialize_index():
    """Initialize the index once at startup"""
    try:
        # Check if index is already initialized in Redis
        if redis_manager.is_initialized():
            logger.info("Using existing index from Redis")
            return index_manager.get_index()
            
        # Try to get existing index
        index = index_manager.get_index()
        if index is not None:
            # Store index state in Redis
            redis_manager.mark_initialized()
            return index
            
        # If index is None, check if we have stored nodes in the database
        stored_nodes = index_manager.node_store.load_nodes()
        if stored_nodes:
            # We have nodes in database but not in the index, let's update the index
            logger.info(f"Found {len(stored_nodes)} nodes in database, building index")
            
            # Reinitialize storage context with existing nodes
            index_manager._init_storage_context()
            
            # Create the index
            index = index_manager.index_documents(stored_nodes)
            # Store index state in Redis
            redis_manager.mark_initialized()
            return index
            
        # If we get here, there's no index and no stored nodes
        # Process documents as a last resort
        nodes = document_processor.process_directory()
        if nodes:
            # Store and index the nodes
            index_manager.node_store.store_nodes(nodes)
            index_manager._init_storage_context()
            index = index_manager.index_documents(nodes)
            # Store index state in Redis
            redis_manager.mark_initialized()
            return index
            
        # If we get here, we have no data at all
        raise HTTPException(
            status_code=500,
            detail="No documents or stored nodes found. Knowledge base is empty."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing index: {str(e)}"
        )

@router.post("/", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    """Process a query against the research papers"""
    try:
        # Get query processor (it will handle initialization if needed)
        query_processor = index_manager.get_query_processor()
        if query_processor is None:
            raise HTTPException(
                status_code=500,
                detail="Index not initialized"
            )
            
        # Process the query
        result = query_processor.process_query(query_request.query)
        
        return result
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing query: {str(e)}"
        )

# Add a method to explicitly refresh the index if needed
@router.post("/refresh-index")
async def refresh_index():
    """Force refresh the index - use when new documents are added"""
    try:
        # Clear Redis state
        redis_manager.clear_all()
        
        # Reinitialize
        await initialize_index()
        
        return {"status": "Index refreshed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing index: {str(e)}"
        )
    
@router.post("/rebuild-all-papers")
async def rebuild_all_papers():
    """Rebuild all papers"""
    try:
        # Clear Redis state
        redis_manager.clear_all()

        # Delete all nodes from database
        index_manager.node_store.delete_all_nodes()

        # Delete the Pinecone index
        index_manager.delete_vector_database()
        
        # Reinitialize
        await initialize_index()
        
        return {"status": "All papers rebuilt successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error rebuilding all papers: {str(e)}"
        )