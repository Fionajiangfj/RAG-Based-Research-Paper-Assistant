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

async def ensure_index_exists():
    """Ensure search index exists and is populated"""
    try:
        # Try to get existing index first
        index = index_manager.get_index()
        if index is not None:
            return index
            
        # If index is None, check if we have stored nodes in the database
        stored_nodes = index_manager.node_store.load_nodes()
        if stored_nodes:
            # We have nodes in database but not in the index, let's update the index
            logger.info(f"Found {len(stored_nodes)} nodes in database, rebuilding index")
            
            # Reinitialize storage context with existing nodes
            index_manager._init_storage_context()
            
            # Create the index (we'll pass stored_nodes as both nodes and leaf_nodes)
            # This will update the vector store with the existing nodes
            index = index_manager.index_documents(stored_nodes, stored_nodes)
            return index
            
        # If we get here, there's no index and no stored nodes
        # Try processing documents as a last resort
        nodes, leaf_nodes = document_processor.process_directory()
        if nodes and leaf_nodes:
            # Store and index the nodes
            index_manager.node_store.store_nodes(nodes)
            index_manager._init_storage_context()
            index = index_manager.index_documents(nodes, leaf_nodes)
            return index
            
        # If we get here, we have no data at all
        raise HTTPException(
            status_code=500,
            detail="No documents or stored nodes found. Knowledge base is empty."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ensuring index exists: {str(e)}"
        )

@router.post("/", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    """Process a query against the research papers"""
    try:
        # Ensure index exists
        index = await ensure_index_exists()
        
        # Create query processor and process query
        query_processor = QueryProcessor(index)
        result = query_processor.process_query(query_request.query)
        
        return result
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing query: {str(e)}"
        ) 