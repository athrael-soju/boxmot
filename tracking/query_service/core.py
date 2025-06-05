"""
Core utilities and configuration for the multi-agent query service.
"""

import os
import logging
from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from neo4j import GraphDatabase, basic_auth

from dotenv import load_dotenv
load_dotenv()

# Configuration
USE_CAPTIONING = os.getenv("USE_CAPTIONING", "False").lower() == "true"
OPENAI_CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4_1-mini-2025-04-14")

# Collection names
ENTITY_COLLECTION_NAME = "entities"
FRAME_COLLECTION_NAME = "frames"
AUDIO_COLLECTION_NAME = "audio_transcripts"
CONVERSATION_COLLECTION_NAME = "conversation_history"

# Global clients
qdrant_client: Optional[QdrantClient] = None
neo4j_driver: Optional[GraphDatabase.driver] = None
embedding_model: Optional[SentenceTransformer] = None

logger = logging.getLogger(__name__)

def initialize_components():
    """Initialize all required components."""
    global qdrant_client, neo4j_driver, embedding_model
    
    logger.info("🔄 Initializing Qdrant client...")
    try:
        # Initialize Qdrant
        qdrant_client = QdrantClient(host='localhost', port=6333)
        # Test connection
        collections = qdrant_client.get_collections()
        logger.info(f"✅ Qdrant connected successfully. Available collections: {[c.name for c in collections.collections]}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Qdrant client: {e}")
        logger.warning("⚠️ Continuing without Qdrant - some features may not work")
        qdrant_client = None
    
    logger.info("🔄 Initializing Neo4j driver...")
    try:
        # Initialize Neo4j
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j") 
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=basic_auth(neo4j_user, neo4j_password))
        # Test connection
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        logger.info("✅ Neo4j connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Neo4j driver: {e}")
        logger.warning("⚠️ Continuing without Neo4j - graph features may not work")
        neo4j_driver = None
    
    logger.info("🔄 Initializing embedding model...")
    try:
        # Initialize embedding model
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "clip-ViT-B-32")
        embedding_model = SentenceTransformer(model_name, device='cpu')
        logger.info(f"✅ Embedding model '{model_name}' loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize embedding model: {e}")
        logger.warning("⚠️ Continuing without embedding model - search features may not work")
        embedding_model = None
    
    logger.info("🎯 Component initialization completed.")

def embed_text(text: str) -> Optional[np.ndarray]:
    """Embed text using SentenceTransformer."""
    if not embedding_model:
        return None
    try:
        embedding = embedding_model.encode([text])
        return embedding[0].astype(np.float32).flatten()
    except Exception as e:
        logger.error(f"Error embedding text: {e}")
        return None

def get_clients():
    """Get initialized client instances."""
    return qdrant_client, neo4j_driver, embedding_model

def get_qdrant_client():
    """Get the initialized Qdrant client."""
    return qdrant_client

def get_neo4j_driver():
    """Get the initialized Neo4j driver."""
    return neo4j_driver

def get_embedding_model():
    """Get the initialized embedding model."""
    return embedding_model 