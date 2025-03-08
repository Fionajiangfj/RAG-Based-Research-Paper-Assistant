import os
import logging
from llama_index.core import Document
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core import SimpleDirectoryReader

from app.core.config import settings
from app.rag.node_store import NodeStore

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[2048, 512, 128]
        )
        self.node_store = NodeStore()
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    def process_file(self, file_path):
        """Process a single file and return nodes"""
        try:
            # Load the document
            documents = SimpleDirectoryReader(
                input_files=[file_path],
                filename_as_id=True
            ).load_data()
            
            if not documents:
                logger.error(f"No content extracted from {file_path}")
                return None, None
            
            # Combine all documents into one
            combined_doc = Document(text="\n\n".join([doc.text for doc in documents]))
            
            # Parse into hierarchical nodes
            nodes = self.node_parser.get_nodes_from_documents([combined_doc])
            leaf_nodes = get_leaf_nodes(nodes)
            
            logger.info(f"Processed {file_path}: {len(nodes)} nodes, {len(leaf_nodes)} leaf nodes")
            
            # Store nodes in database
            self.node_store.store_nodes(nodes)
            
            return nodes, leaf_nodes
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    def process_directory(self):
        """Process all PDF files in the upload directory"""
        try:
            # Load all PDF files from the directory
            documents = SimpleDirectoryReader(
                input_dir=self.upload_dir,
                recursive=True,
                filename_as_id=True,
                required_exts=['.pdf']
            ).load_data()
            
            if not documents:
                logger.warning(f"No documents found in {self.upload_dir}")
                return None, None
            
            # Combine all documents into one
            combined_doc = Document(text="\n\n".join([doc.text for doc in documents]))
            
            # Parse into hierarchical nodes
            nodes = self.node_parser.get_nodes_from_documents([combined_doc])
            leaf_nodes = get_leaf_nodes(nodes)
            
            logger.info(f"Processed directory {self.upload_dir}: {len(nodes)} nodes, {len(leaf_nodes)} leaf nodes")
            
            # Store nodes in database
            self.node_store.store_nodes(nodes)
            
            return nodes, leaf_nodes
        
        except Exception as e:
            logger.error(f"Error processing directory {self.upload_dir}: {str(e)}")
            raise 