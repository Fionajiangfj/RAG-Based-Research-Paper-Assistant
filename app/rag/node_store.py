import logging
from sqlalchemy.orm import Session
import json
from app.db.database import Document, SessionLocal
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
                    existing_doc = db.query(Document).filter(
                        Document.doc_id == node.node_id
                    ).first()
                    
                    if existing_doc:
                        existing_doc.content = node.text
                        existing_doc.node_metadata = json.dumps(node.metadata) if node.metadata else None
                    else:
                        doc = Document(
                            doc_id=node.node_id,
                            content=node.text,
                            node_metadata=json.dumps(node.metadata) if node.metadata else None
                        )
                        db.add(doc)
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
                    stored_docs = db.query(Document).all()
                    nodes = []
                    for doc in stored_docs:
                        llama_doc = LlamaDocument(
                            doc_id=doc.doc_id,
                            text=doc.content,
                            metadata=json.loads(doc.node_metadata) if doc.node_metadata else {}
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
                db.query(Document).filter(
                    Document.doc_id.notin_(doc_ids)
                ).delete(synchronize_session=False)
                db.commit()
                logger.info("Cleaned up old nodes from database")
        except Exception as e:
            logger.error(f"Error cleaning up nodes: {str(e)}")
            raise 