import logging
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.query_engine import RetrieverQueryEngine

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, index):
        self.index = index
        self.query_engine = self._build_query_engine()
    
    def _build_query_engine(self):
        """Build the query engine with reranking but without auto-merging"""
        try:
            # Create base retriever with higher top_k
            retriever = self.index.as_retriever(
                similarity_top_k=12
            )
            
            # Create reranker
            rerank = SentenceTransformerRerank(
                top_n=6, 
                model="BAAI/bge-reranker-base"
            )
            
            # Create query engine without auto-merging
            query_engine = RetrieverQueryEngine.from_args(
                retriever, 
                node_postprocessors=[rerank]
            )
            
            logger.info("Query engine built successfully")
            return query_engine
            
        except Exception as e:
            logger.error(f"Error building query engine: {str(e)}")
            raise
    
    def process_query(self, query_text):
        """Process a query and return results"""
        try:
            logger.info(f"Processing query: {query_text}")
            logger.info("Attempting to query the engine...")
            response = self.query_engine.query(query_text)
            logger.info("Query completed successfully")

            if hasattr(response, 'source_nodes'):
                logger.info(f"Number of source nodes: {len(response.source_nodes)}")
                for idx, node in enumerate(response.source_nodes):
                    logger.info(f"Source node {idx + 1}:")
                    # Handle different node types
                    if hasattr(node, 'node'):
                        text = node.node.get_text() if hasattr(node.node, 'text') else str(node.node)
                        logger.info(f"  Text: {text[:200]}...")  # First 200 chars
                    if hasattr(node, 'score'):
                        logger.info(f"  Score: {node.score}")
                    if hasattr(node, 'node') and hasattr(node.node, 'node_id'):
                        logger.info(f"  Doc ID: {node.node.node_id}")
                    if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                        logger.info(f"  Has metadata: True")
                        logger.info(f"  Metadata keys: {list(node.node.metadata.keys())}")
                    else:
                        logger.info("  No metadata found")

            return {
                "answer": str(response),
                "source_nodes": [
                    {
                        "text": node.node.get_text() if hasattr(node, 'node') and hasattr(node.node, 'get_text') else str(node),
                        "score": node.score if hasattr(node, 'score') else None,
                        "doc_id": node.node.metadata.get('arxiv_id') if hasattr(node, 'node') and hasattr(node.node, 'metadata') and isinstance(node.node.metadata, dict) else None,
                        "arxiv_url": node.node.metadata.get('arxiv_url') if hasattr(node, 'node') and hasattr(node.node, 'metadata') and isinstance(node.node.metadata, dict) else None,
                        "filename": node.node.metadata.get('filename') if hasattr(node, 'node') and hasattr(node.node, 'metadata') and isinstance(node.node.metadata, dict) else None,
                        "arxiv_id": node.node.metadata.get('arxiv_id') if hasattr(node, 'node') and hasattr(node.node, 'metadata') and isinstance(node.node.metadata, dict) else None
                    }
                    for node in response.source_nodes
                ]
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise 