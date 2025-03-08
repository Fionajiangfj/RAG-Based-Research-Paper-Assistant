import os
import shutil
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.config import settings
from app.rag.document_processor import DocumentProcessor
from app.rag.index_manager import IndexManager

router = APIRouter()
document_processor = DocumentProcessor()
index_manager = IndexManager()

@router.post("/upload/")
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a research paper (PDF)"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save the file
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Process and index the file in the background
    background_tasks.add_task(process_and_index_file, file_path)
    
    return {"filename": file.filename, "status": "File uploaded successfully. Processing in background."}

async def process_and_index_file(file_path: str):
    """Process and index a file in the background"""
    try:
        # Process the file
        nodes, leaf_nodes = document_processor.process_file(file_path)
        if nodes and leaf_nodes:
            # Index the documents
            index_manager.index_documents(nodes, leaf_nodes)
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")

@router.post("/reindex/")
async def reindex_all_papers(background_tasks: BackgroundTasks):
    """Reindex all papers in the upload directory"""
    background_tasks.add_task(process_and_index_all)
    return {"status": "Reindexing started in background"}

async def process_and_index_all():
    """Process and index all files in the background"""
    try:
        # Process all files in the directory
        nodes, leaf_nodes = document_processor.process_directory()
        if nodes and leaf_nodes:
            # Get list of current doc_ids
            current_doc_ids = [node.node_id for node in nodes]
            
            # Index the documents
            index_manager.index_documents(nodes, leaf_nodes)
            
            # Cleanup old documents
            index_manager.cleanup_documents(current_doc_ids)
    except Exception as e:
        print(f"Error processing directory: {str(e)}") 