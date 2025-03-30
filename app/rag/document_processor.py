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
            # Extract filename and arxiv_id from file_path
            filename = os.path.basename(file_path)
            arxiv_id = os.path.splitext(filename)[0]  # Remove .pdf extension
            arxiv_url = f"https://arxiv.org/pdf/{arxiv_id}"
            
            # Load the document
            documents = SimpleDirectoryReader(
                input_files=[file_path],
                filename_as_id=True
            ).load_data()
            
            if not documents:
                logger.error(f"No content extracted from {file_path}")
                return None, None
            
            # Clean text by creating new documents without null characters
            cleaned_docs = []
            for doc in documents:
                # Replace null characters with empty string
                cleaned_text = doc.text.replace('\x00', '')
                # Create new Document with updated metadata
                metadata = {
                    'arxiv_url': arxiv_url
                }
                new_doc = Document(text=cleaned_text, metadata=metadata)
                cleaned_docs.append(new_doc)
            
            # Combine all documents into one while preserving metadata from the first document
            combined_doc = Document(
                text="\n\n".join([doc.text for doc in cleaned_docs]),
                metadata=cleaned_docs[0].metadata if cleaned_docs else {}
            )
            
            # Parse into hierarchical nodes
            nodes = self.node_parser.get_nodes_from_documents([combined_doc])
            leaf_nodes = get_leaf_nodes(nodes)
            
            # Ensure metadata is passed to leaf nodes
            for node in leaf_nodes:
                node.metadata = combined_doc.metadata
            
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
            
            # Clean text by creating new documents without null characters
            cleaned_docs = []
            for doc in documents:
                # Replace null characters with empty string
                cleaned_text = doc.text.replace('\x00', '')
                
                # Extract metadata from file path
                file_path = doc.metadata.get('file_path', '') if doc.metadata else ''
                filename = os.path.basename(file_path)
                arxiv_id = os.path.splitext(filename)[0]  # Remove .pdf extension
                arxiv_url = f"https://arxiv.org/pdf/{arxiv_id}"
                
                # Create new Document with updated metadata
                metadata = {
                    'arxiv_url': arxiv_url
                }
                new_doc = Document(text=cleaned_text, metadata=metadata)
                cleaned_docs.append(new_doc)
            
            # Combine all documents into one while preserving metadata from the first document
            combined_doc = Document(
                text="\n\n".join([doc.text for doc in cleaned_docs]),
                metadata=cleaned_docs[0].metadata if cleaned_docs else {}
            )
            
            # Parse into hierarchical nodes
            nodes = self.node_parser.get_nodes_from_documents([combined_doc])
            leaf_nodes = get_leaf_nodes(nodes)
            
            # Ensure metadata is passed to leaf nodes
            for node in leaf_nodes:
                node.metadata = combined_doc.metadata
            
            logger.info(f"Processed directory {self.upload_dir}: {len(nodes)} nodes, {len(leaf_nodes)} leaf nodes")
            
            # Store nodes in database
            self.node_store.store_nodes(nodes)
            
            return nodes, leaf_nodes
        
        except Exception as e:
            logger.error(f"Error processing directory {self.upload_dir}: {str(e)}")
            raise 