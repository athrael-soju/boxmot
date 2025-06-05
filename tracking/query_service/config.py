"""
Configuration for the Query Service
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

@dataclass
class QueryServiceConfig:
    """Configuration class for the query service"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    
    # Vector Database Configuration
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Graph Database Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # MinIO Configuration
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket_name: str = os.getenv("MINIO_BUCKET_NAME", "boxmot-images")
    minio_use_ssl: bool = os.getenv("MINIO_USE_SSL", "False").lower() == "true"
    
    # Embedding Configuration
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "clip-ViT-B-32")
    use_captioning: bool = os.getenv("USE_CAPTIONING", "False").lower() == "true"
    
    # Query Service Configuration
    max_query_iterations: int = 5
    similarity_threshold: float = 0.3
    max_results_per_query: int = 10
    
    # Agent Configuration
    enable_tracing: bool = True
    conversation_timeout: int = 300  # 5 minutes
    
    def validate(self) -> bool:
        """Validate the configuration"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        return True 