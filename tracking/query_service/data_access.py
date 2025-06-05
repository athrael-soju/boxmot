"""
Data Access Layer for Query Service

This module provides unified access to all data sources:
- Vector databases (Qdrant)
- Graph database (Neo4j)
- Object storage (MinIO)
- Embedding models
"""

import logging
import io
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from minio import Minio
from minio.error import S3Error

from .config import QueryServiceConfig

logger = logging.getLogger(__name__)

class DataAccessLayer:
    """Unified data access layer for all query service operations"""
    
    def __init__(self, config: QueryServiceConfig):
        self.config = config
        self._embedding_model: Optional[SentenceTransformer] = None
        self._qdrant_client: Optional[QdrantClient] = None
        self._neo4j_driver = None
        self._minio_client: Optional[Minio] = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all database and service clients"""
        try:
            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.config.embedding_model_name}")
            self._embedding_model = SentenceTransformer(self.config.embedding_model_name, device='cpu')
            self._embedding_model.eval()
            
            # Initialize Qdrant client
            logger.info(f"Connecting to Qdrant at {self.config.qdrant_host}:{self.config.qdrant_port}")
            self._qdrant_client = QdrantClient(host=self.config.qdrant_host, port=self.config.qdrant_port)
            
            # Initialize Neo4j driver
            logger.info(f"Connecting to Neo4j at {self.config.neo4j_uri}")
            self._neo4j_driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            self._neo4j_driver.verify_connectivity()
            
            # Initialize MinIO client
            if not self.config.use_captioning:
                logger.info(f"Connecting to MinIO at {self.config.minio_endpoint}")
                self._minio_client = Minio(
                    self.config.minio_endpoint,
                    access_key=self.config.minio_access_key,
                    secret_key=self.config.minio_secret_key,
                    secure=self.config.minio_use_ssl
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize data access layer: {e}")
            raise
    
    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Generate text embedding"""
        if not self._embedding_model:
            return None
        try:
            embedding = self._embedding_model.encode([text])
            return embedding[0].astype(np.float32).flatten()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return None
    
    def search_entities(self, query_embedding: np.ndarray, limit: int = 10, 
                       threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search for entities in Qdrant"""
        if not self._qdrant_client:
            return []
        
        try:
            results = self._qdrant_client.query_points(
                collection_name="entities",
                query=query_embedding.tolist(),
                limit=limit,
                score_threshold=threshold,
                with_payload=True
            )
            
            entities = []
            for hit in results.points:
                entity_info = {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload or {}
                }
                entities.append(entity_info)
            
            return entities
        except Exception as e:
            logger.error(f"Error searching entities: {e}")
            return []
    
    def search_frames(self, query_embedding: np.ndarray, limit: int = 10,
                     threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search for frames in Qdrant"""
        if not self._qdrant_client:
            return []
        
        try:
            results = self._qdrant_client.query_points(
                collection_name="frames",
                query=query_embedding.tolist(),
                limit=limit,
                score_threshold=threshold,
                with_payload=True
            )
            
            frames = []
            for hit in results.points:
                frame_info = {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload or {}
                }
                frames.append(frame_info)
            
            return frames
        except Exception as e:
            logger.error(f"Error searching frames: {e}")
            return []
    
    def search_audio_transcripts(self, query_embedding: np.ndarray, limit: int = 10,
                               threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search for audio transcripts in Qdrant"""
        if not self._qdrant_client:
            return []
        
        try:
            results = self._qdrant_client.query_points(
                collection_name="audio_transcripts",
                query=query_embedding.tolist(),
                limit=limit,
                score_threshold=threshold,
                with_payload=True
            )
            
            transcripts = []
            for hit in results.points:
                transcript_info = {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload or {}
                }
                transcripts.append(transcript_info)
            
            return transcripts
        except Exception as e:
            logger.error(f"Error searching audio transcripts: {e}")
            return []
    
    def execute_cypher_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query against Neo4j"""
        if not self._neo4j_driver:
            return []
        
        try:
            with self._neo4j_driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return []
    
    def get_entity_relationships(self, entity_ids: List[str]) -> Dict[str, Any]:
        """Get relationships for specific entities"""
        if not entity_ids or not self._neo4j_driver:
            return {}
        
        try:
            with self._neo4j_driver.session() as session:
                # Get direct relationships between entities
                query = """
                MATCH (e1:Entity)-[r]-(e2:Entity)
                WHERE e1.entity_id IN $entity_ids AND e2.entity_id IN $entity_ids
                RETURN e1.entity_id as entity1, type(r) as relationship, e2.entity_id as entity2
                """
                result = session.run(query, entity_ids=entity_ids)
                
                relationships = []
                for record in result:
                    relationships.append({
                        "entity1": record["entity1"],
                        "relationship": record["relationship"],
                        "entity2": record["entity2"]
                    })
                
                return {"relationships": relationships}
        except Exception as e:
            logger.error(f"Error getting entity relationships: {e}")
            return {}
    
    def get_entity_summary(self, entity_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for an entity"""
        if not self._neo4j_driver:
            return {}
        
        try:
            with self._neo4j_driver.session() as session:
                query = """
                MATCH (e:Entity {entity_id: $entity_id})
                OPTIONAL MATCH (e)-[:DETECTED_IN]->(f:Frame)
                WITH e, collect(DISTINCT f.frame_idx) as frames
                OPTIONAL MATCH (e)-[r]-(other:Entity)
                WHERE e.entity_id <> other.entity_id
                RETURN e.name as name, e.entity_id as id, frames,
                       collect(DISTINCT {type: type(r), target: other.entity_id, target_name: other.name}) as relationships
                """
                result = session.run(query, entity_id=entity_id)
                record = result.single()
                
                if record:
                    return {
                        "entity_id": record["id"],
                        "name": record["name"],
                        "frames": sorted(record["frames"]),
                        "relationships": record["relationships"]
                    }
                return {}
        except Exception as e:
            logger.error(f"Error getting entity summary: {e}")
            return {}
    
    def count_entities_by_class(self) -> Dict[str, int]:
        """Count entities by class name"""
        try:
            with self._neo4j_driver.session() as session:
                query = """
                MATCH (e:Entity)
                RETURN e.class_name as class_name, count(e) as count
                ORDER BY count DESC
                """
                result = session.run(query)
                return {record["class_name"]: record["count"] for record in result}
        except Exception as e:
            logger.error(f"Error counting entities by class: {e}")
            return {}
    
    def get_temporal_analysis(self, start_frame: int = None, end_frame: int = None) -> Dict[str, Any]:
        """Get temporal analysis of entity appearances"""
        try:
            with self._neo4j_driver.session() as session:
                query = """
                MATCH (e:Entity)-[:DETECTED_IN]->(f:Frame)
                WHERE ($start_frame IS NULL OR f.frame_idx >= $start_frame)
                  AND ($end_frame IS NULL OR f.frame_idx <= $end_frame)
                WITH e, collect(f.frame_idx) as frame_indices
                RETURN e.entity_id as entity_id, e.name as name, e.class_name as class_name,
                       size(frame_indices) as appearance_count,
                       min(frame_indices) as first_frame,
                       max(frame_indices) as last_frame
                ORDER BY appearance_count DESC
                """
                result = session.run(query, start_frame=start_frame, end_frame=end_frame)
                
                entities = []
                for record in result:
                    entities.append({
                        "entity_id": record["entity_id"],
                        "name": record["name"],
                        "class_name": record["class_name"],
                        "appearance_count": record["appearance_count"],
                        "first_frame": record["first_frame"],
                        "last_frame": record["last_frame"]
                    })
                
                return {"temporal_analysis": entities}
        except Exception as e:
            logger.error(f"Error getting temporal analysis: {e}")
            return {}
    
    def download_image_from_minio(self, object_name: str) -> Optional[bytes]:
        """Download image from MinIO"""
        if not self._minio_client or self.config.use_captioning:
            return None
        
        try:
            response = self._minio_client.get_object(self.config.minio_bucket_name, object_name)
            image_bytes = response.read()
            response.close()
            response.release_conn()
            return image_bytes
        except S3Error as e:
            logger.error(f"Error downloading image from MinIO: {e}")
            return None
    
    def close(self):
        """Close all connections"""
        if self._neo4j_driver:
            self._neo4j_driver.close()
        # Qdrant and MinIO clients don't need explicit closing 