import redis
import pickle
import logging
import os
from typing import Optional, List, Dict, Any
from llama_index.core.schema import Node

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        # Use REDIS_URL from environment if available
        redis_url = os.environ.get("REDIS_URL")
        
        if redis_url:
            logger.info(f"Connecting to Redis using URL from environment")
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False  # Keep binary data as is
            )
        else:
            logger.info(f"Connecting to Redis at {host}:{port}")
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=False  # Keep binary data as is
            )
            
        self.initialization_key = "initialization_complete"
        self.nodes_key = "nodes"
        self.index_stats_key = "index_stats"

    def is_initialized(self) -> bool:
        """Check if the system has been initialized"""
        return bool(self.redis_client.get(self.initialization_key))

    def mark_initialized(self):
        """Mark the system as initialized"""
        self.redis_client.set(self.initialization_key, "true")
        logger.info("Marked system as initialized in Redis")

    def store_nodes(self, nodes: List[Node]):
        """Store nodes in Redis"""
        try:
            serialized_nodes = pickle.dumps(nodes)
            self.redis_client.set(self.nodes_key, serialized_nodes)
            logger.info(f"Stored {len(nodes)} nodes in Redis")
        except Exception as e:
            logger.error(f"Error storing nodes in Redis: {str(e)}")
            raise

    def get_nodes(self) -> Optional[List[Node]]:
        """Retrieve nodes from Redis"""
        try:
            data = self.redis_client.get(self.nodes_key)
            if data:
                nodes = pickle.loads(data)
                logger.info(f"Retrieved {len(nodes)} nodes from Redis")
                return nodes
            return None
        except Exception as e:
            logger.error(f"Error retrieving nodes from Redis: {str(e)}")
            return None

    def store_index_stats(self, stats: Dict[str, Any]):
        """Store index statistics in Redis"""
        try:
            self.redis_client.set(self.index_stats_key, pickle.dumps(stats))
            # logger.info("Stored index stats in Redis")
        except Exception as e:
            logger.error(f"Error storing index stats in Redis: {str(e)}")
            raise

    def get_index_stats(self) -> Optional[Dict[str, Any]]:
        """Retrieve index statistics from Redis"""
        try:
            data = self.redis_client.get(self.index_stats_key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving index stats from Redis: {str(e)}")
            return None

    def clear_all(self):
        """Clear all Redis data"""
        try:
            self.redis_client.delete(self.initialization_key, self.nodes_key, self.index_stats_key)
            logger.info("Cleared all Redis data")
        except Exception as e:
            logger.error(f"Error clearing Redis data: {str(e)}")
            raise

    def cleanup(self):
        """Clean up Redis resources"""
        try:
            self.redis_client.close()
            logger.info("Closed Redis connection")
        except Exception as e:
            logger.error(f"Error cleaning up Redis resources: {str(e)}")
            raise 