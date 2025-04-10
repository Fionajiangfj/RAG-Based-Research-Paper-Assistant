import time
import logging
from pinecone import Pinecone, ServerlessSpec, DeletionProtection
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

import json
import threading
import os

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Node
from app.rag.node_store import NodeStore
from app.rag.redis_manager import RedisManager
from app.rag.query_engine import QueryProcessor

logger = logging.getLogger(__name__)

# Global lock for Redis operations
redis_lock = threading.Lock()

class IndexManager:
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX_NAME
        self.environment = settings.PINECONE_ENVIRONMENT
        self.pinecone_client = None
        self.pinecone_index = None
        self.vector_store = None
        self.storage_context = None
        self.node_store = NodeStore()
        self.redis_manager = RedisManager()
        self._query_processor = None
        
        # Initialize Ollama model and set it globally
        llm = Ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            request_timeout=300.0
        )
        self.embed_model = OpenAIEmbedding()
        Settings.llm = llm
        Settings.embed_model = self.embed_model
        
        # Initialize Pinecone
        self._init_pinecone()
        self._init_storage_context()
    
    def _init_pinecone(self):
        """Initialize Pinecone client and index"""
        try:
            self.pinecone_client = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            existing_indexes = [
                index_info["name"] for index_info in self.pinecone_client.list_indexes()
            ]
            
            # Create index if it doesn't exist
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pinecone_client.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI text-embedding-ada-002 dimension
                    metric="cosine",
                    deletion_protection=DeletionProtection.DISABLED,
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.environment
                    )
                )
                # Wait for index to be initialized
                while not self.pinecone_client.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
            
            # Connect to index
            self.pinecone_index = self.pinecone_client.Index(self.index_name)
            
            # Initialize vector store with OpenAI embedding model
            self.vector_store = PineconeVectorStore(
                pinecone_index=self.pinecone_index,
                text_key="text"
            )
            
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {str(e)}")
            raise
    
    def _init_storage_context(self):
        """Initialize storage context with existing nodes"""
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # Use lock to prevent multiple workers from loading nodes simultaneously
        with redis_lock:
            # Check if nodes are already in Redis
            nodes = self.redis_manager.get_nodes()
            if not nodes:
                # If not in Redis, load from database and store in Redis
                nodes = self.node_store.load_nodes()
                if nodes:
                    self.redis_manager.store_nodes(nodes)
                    self.storage_context.docstore.add_documents(nodes)
                    logger.info(f"Initialized storage context with {len(nodes)} documents")
            else:
                # Use nodes from Redis
                self.storage_context.docstore.add_documents(nodes)
                logger.info(f"Initialized storage context with {len(nodes)} documents from Redis")
    
    def get_query_processor(self):
        """Get or create query processor"""
        if self._query_processor is None:
            index = self.get_index()
            if index is not None:
                self._query_processor = QueryProcessor(index)
        return self._query_processor
    
    def index_documents(self, nodes):
        """Index documents to Pinecone"""
        try:
            # Only create embeddings if the index is empty
            index_stats = self.pinecone_index.describe_index_stats()
            
            # Always update storage context with all nodes
            # self.storage_context.docstore.add_documents(nodes)
            
            # Use lock to prevent multiple workers from storing in Redis simultaneously
            with redis_lock:
                # Store nodes in Redis
                self.redis_manager.store_nodes(nodes)
                logger.info(f"Added {len(nodes)} nodes to storage context and Redis")
            
            if index_stats.total_vector_count == 0:
                logger.info("Index is empty, indexing documents")
                # Create vector store index with existing storage context
                index = VectorStoreIndex(
                    nodes,
                    storage_context=self.storage_context
                )
            else:
                logger.info("Index already contains vectors, using existing embeddings")
                # Use existing storage context and vector store
                index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store,
                    storage_context=self.storage_context
                )
            
            # Store index stats in Redis with lock
            with redis_lock:
                self.redis_manager.store_index_stats(index_stats)
            
            return index
            
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            raise
    
    def get_index(self):
        """Get existing index from Pinecone with Redis caching"""
        try:
            # Fast path: Use Redis cache if available
            if self.redis_manager.is_initialized():
                logger.info("Using cached index from Redis")
                return VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store,
                    storage_context=self.storage_context
                )
            
            # Check Pinecone index status
            index_stats = self.pinecone_index.describe_index_stats()
            if index_stats.total_vector_count == 0:
                logger.warning("Pinecone index is empty")
                return None
            
            # Rebuild storage context and load nodes
            logger.info("Rebuilding storage context from database")
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            nodes = self.node_store.load_nodes()
            if not nodes:
                logger.warning("No nodes found in database")
                return None
            
            # Update storage and cache
            self.storage_context.docstore.add_documents(nodes)
            with redis_lock:
                self.redis_manager.store_nodes(nodes)
                self.redis_manager.store_index_stats(index_stats)
                self.redis_manager.mark_initialized()
                logger.info(f"Loaded {len(nodes)} documents into storage and cache")
            
            # Create and return index
            return VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context
            )
            
        except Exception as e:
            logger.error(f"Error getting index: {str(e)}")
            raise

    def cleanup_documents(self, doc_ids):
        """Remove documents that no longer exist"""
        try:
            with SessionLocal() as db:
                # Delete documents not in the current set
                db.query(Node).filter(
                    Node.node.notin_(doc_ids)
                ).delete(synchronize_session=False)
                db.commit()
                logger.info("Cleaned up old documents from database")
        except Exception as e:
            logger.error(f"Error cleaning up documents: {str(e)}")
            raise

    def delete_vector_database(self):
        """Delete the entire Pinecone index"""
        try:
            # Delete the entire index
            self.pinecone_client.delete_index(self.index_name)
            # Clear Redis data with lock
            with redis_lock:
                self.redis_manager.clear_all()
            logger.info(f"Deleted Pinecone index: {self.index_name} and cleared Redis data")
        except Exception as e:
            logger.error(f"Error deleting Pinecone index: {str(e)}")
            raise