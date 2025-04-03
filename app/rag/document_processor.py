import os
import logging
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader
from llama_index.core import Settings

from app.core.config import settings
from app.rag.node_store import NodeStore

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.node_store = NodeStore()
        
        # Initialize sentence splitter
        self.text_splitter = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=10
        )
        
        # Set text splitter globally
        Settings.text_splitter = self.text_splitter
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    
    def process_directory(self):
        """Process all PDF files in the upload directory"""
        try:
            # Load all PDF files from the directory
            documents = SimpleDirectoryReader(
                input_dir=self.upload_dir,
                recursive=True,
                filename_as_id=True,
                required_exts=['.pdf'],
            ).load_data()
            
            if not documents:
                logger.warning(f"No documents found in {self.upload_dir}")
                return None
            
            # Process each document separately
            all_nodes = []
            doc_ids = []
            
            for doc in documents:
                # Replace null characters with empty string
                cleaned_text = doc.text.replace('\x00', '')
                
                # Extract metadata from file path
                file_path = doc.metadata.get('file_path', '') if doc.metadata else ''
                filename = os.path.basename(file_path)
                arxiv_id = os.path.splitext(filename)[0]  # Remove .pdf extension
                arxiv_url = f"https://arxiv.org/pdf/{arxiv_id}"
                
                # Create metadata for this specific document
                metadata = {
                    'arxiv_url': arxiv_url,
                    'filename': filename,
                    'arxiv_id': arxiv_id
                }
                
                # Create a document with cleaned text and metadata
                clean_doc = Document(text=cleaned_text, metadata=metadata)
                
                # Parse this document into nodes
                doc_nodes = self.text_splitter.get_nodes_from_documents([clean_doc])
                
                logger.info(f"Processed document {filename}: {len(doc_nodes)} nodes")
                
                # Store document ID to avoid deletion
                doc_ids.append(arxiv_id)
                
                # Add nodes to the collection
                all_nodes.extend(doc_nodes)
            
            logger.info(f"Processed directory {self.upload_dir}: {len(all_nodes)} total nodes")
            
            # Store nodes in database
            self.node_store.store_nodes(all_nodes)
            
            return all_nodes
        
        except Exception as e:
            logger.error(f"Error processing directory {self.upload_dir}: {str(e)}")
            raise 