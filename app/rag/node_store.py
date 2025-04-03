import logging
from sqlalchemy.orm import Session
import json
from app.db.database import SessionLocal
from app.db.models import Node
from llama_index.core import Document as LlamaDocument

logger = logging.getLogger(__name__)

class NodeStore:
    def __init__(self):
        self.storage_context = None
    
    def store_nodes(self, nodes):
        """Store nodes in database"""
        try:
            with SessionLocal() as db:
                for node in nodes:
                    logger.info(f"Storing node {node.node_id}")
                    logger.info(f"Node metadata before storage: {node.metadata}")
                    existing_doc = db.query(Node).filter(
                        Node.node_id == node.node_id
                    ).first()
                    
                    if existing_doc:
                        existing_doc.node_text = node.text
                        existing_doc.node_metadata = json.dumps(node.metadata) if node.metadata else None
                        logger.info(f"Updated existing doc {node.node_id} with metadata: {node.metadata}")
                    else:
                        doc = Node(
                            node_id=node.node_id,
                            node_text=node.text,
                            node_metadata=json.dumps(node.metadata) if node.metadata else None
                        )
                        db.add(doc)
                        logger.info(f"Created new doc {node.node_id} with metadata: {node.metadata}")
                db.commit()
                logger.info(f"Stored {len(nodes)} nodes in database")
                return True
        except Exception as e:
            logger.error(f"Error storing nodes: {str(e)}")
            raise

    def load_nodes(self):
        """Load nodes from database into storage context"""
        try:
            with SessionLocal() as db:
                try:
                    stored_docs = db.query(Node).all()
                    nodes = []
                    for doc in stored_docs:
                        logger.info(f"Loading doc {doc.node_id}")
                        logger.info(f"Raw metadata from DB: {doc.node_metadata}")
                        metadata = json.loads(doc.node_metadata) if doc.node_metadata else {}
                        logger.info(f"Parsed metadata: {metadata}")
                        llama_doc = LlamaDocument(
                            doc_id=doc.node_id,
                            text=doc.node_text,
                            metadata=metadata
                        )
                        nodes.append(llama_doc)
                    logger.info(f"Loaded {len(nodes)} nodes from database")
                    return nodes
                except Exception as e:
                    logger.warning(f"Could not load nodes from database: {str(e)}")
                    return []  # Return empty list if table doesn't exist or other error
        except Exception as e:
            logger.error(f"Error loading nodes: {str(e)}")
            raise

    def cleanup_nodes(self, doc_ids):
        """Remove nodes that no longer exist"""
        try:
            with SessionLocal() as db:
                db.query(Node).filter(
                    Node.node_id.notin_(doc_ids)
                ).delete(synchronize_session=False)
                db.commit()
                logger.info("Cleaned up old nodes from database")
        except Exception as e:
            logger.error(f"Error cleaning up nodes: {str(e)}")
            raise 

    def delete_all_nodes(self):
        """Delete all nodes from database"""
        try:
            with SessionLocal() as db:
                db.query(Node).delete(synchronize_session=False)
                db.commit()
                logger.info("Deleted all nodes from database")
        except Exception as e:
            logger.error(f"Error deleting all nodes: {str(e)}")
            raise