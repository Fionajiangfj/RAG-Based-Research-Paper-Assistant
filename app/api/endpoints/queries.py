import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.rag.index_manager import IndexManager
from app.rag.query_engine import QueryProcessor
from app.rag.document_processor import DocumentProcessor

router = APIRouter()
index_manager = IndexManager()
document_processor = DocumentProcessor()

# Global variables to store the index and query processor
global_index = None
global_query_processor = None

logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str

class SourceNode(BaseModel):
    text: str
    score: Optional[float] = None
    doc_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    source_nodes: List[SourceNode] = []

async def initialize_index():
    """Initialize the index once at startup"""
    global global_index, global_query_processor
    
    if global_index is not None:
        return global_index
        
    try:
        # Try to get existing index
        index = index_manager.get_index()
        if index is not None:
            global_index = index
            global_query_processor = QueryProcessor(global_index)
            return global_index
            
        # If index is None, check if we have stored nodes in the database
        stored_nodes = index_manager.node_store.load_nodes()
        if stored_nodes:
            # We have nodes in database but not in the index, let's update the index
            logger.info(f"Found {len(stored_nodes)} nodes in database, building index")
            
            # Reinitialize storage context with existing nodes
            index_manager._init_storage_context()
            
            # Create the index
            index = index_manager.index_documents(stored_nodes, stored_nodes)
            global_index = index
            global_query_processor = QueryProcessor(global_index)
            return global_index
            
        # If we get here, there's no index and no stored nodes
        # Process documents as a last resort
        nodes, leaf_nodes = document_processor.process_directory()
        if nodes and leaf_nodes:
            # Store and index the nodes
            index_manager.node_store.store_nodes(nodes)
            index_manager._init_storage_context()
            index = index_manager.index_documents(nodes, leaf_nodes)
            global_index = index
            global_query_processor = QueryProcessor(global_index)
            return global_index
            
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
    global global_index, global_query_processor
    
    try:
        # Initialize index if not already done
        if global_index is None:
            await initialize_index()
            
        # Use the global query processor
        result = global_query_processor.process_query(query_request.query)
        
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
    global global_index, global_query_processor
    
    try:
        # Reset the globals
        global_index = None
        global_query_processor = None
        
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