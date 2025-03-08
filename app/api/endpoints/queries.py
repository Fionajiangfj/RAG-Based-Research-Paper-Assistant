from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.rag.index_manager import IndexManager
from app.rag.query_engine import QueryProcessor
from app.rag.document_processor import DocumentProcessor

router = APIRouter()
index_manager = IndexManager()
document_processor = DocumentProcessor()

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
        index = index_manager.get_index()
        if index is None:
            # Process all documents
            nodes, leaf_nodes = document_processor.process_directory()
            if not nodes or not leaf_nodes:
                raise HTTPException(
                    status_code=500,
                    detail="No documents found to process"
                )
            
            # Verify nodes are stored and update index
            stored_nodes = index_manager.node_store.load_nodes()
            if not stored_nodes:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to store document nodes in database"
                )
            
            # Reinitialize storage context with new nodes
            index_manager._init_storage_context()
            
            # Create the index
            index = index_manager.index_documents(nodes, leaf_nodes)
            if not index:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create search index"
                )
        
        return index
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