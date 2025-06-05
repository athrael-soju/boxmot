"""
Tool functions for the multi-agent query service.
"""

import json
import uuid
from typing import List
from datetime import datetime
from agents import function_tool
from qdrant_client import models

from .core import (
    embed_text, 
    get_qdrant_client,
    get_neo4j_driver,
    ENTITY_COLLECTION_NAME,
    FRAME_COLLECTION_NAME, 
    AUDIO_COLLECTION_NAME,
    CONVERSATION_COLLECTION_NAME,
    USE_CAPTIONING,
    logger
)

@function_tool
def retrieve_visual_content(query: str, limit: int = 5) -> str:
    """Retrieve visual content from vector database."""
    logger.info(f"🔍 [TOOL] retrieve_visual_content called with query: '{query}', limit: {limit}")
    
    query_embedding = embed_text(query)
    qdrant_client = get_qdrant_client()
    if query_embedding is None or not qdrant_client:
        logger.warning("🔍 [TOOL] retrieve_visual_content: embedding model or database not available")
        return "Unable to process query - embedding model or database not available."
    
    try:
        logger.info(f"🔍 [TOOL] Searching {ENTITY_COLLECTION_NAME} collection...")
        # Search entities
        entity_hits = qdrant_client.query_points(
            collection_name=ENTITY_COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=limit,
            with_payload=True
        )
        
        logger.info(f"🔍 [TOOL] Found {len(entity_hits.points)} entity hits")
        
        results = []
        for hit in entity_hits.points:
            payload = hit.payload or {}
            results.append({
                "type": "entity",
                "score": hit.score,
                "entity_id": payload.get("entity_id"),
                "class_name": payload.get("class_name"),
                "caption": payload.get("image_caption") if USE_CAPTIONING else None
            })
        
        result_json = json.dumps(results, indent=2)
        logger.info(f"🔍 [TOOL] retrieve_visual_content returning {len(results)} results")
        return result_json
    except Exception as e:
        logger.error(f"🔍 [TOOL] Error retrieving visual content: {e}")
        return f"Error retrieving visual content: {str(e)}"

@function_tool  
def retrieve_audio_content(query: str, limit: int = 3) -> str:
    """Retrieve audio transcripts from vector database."""
    logger.info(f"🎵 [TOOL] retrieve_audio_content called with query: '{query}', limit: {limit}")
    
    query_embedding = embed_text(query)
    qdrant_client = get_qdrant_client()
    if query_embedding is None or not qdrant_client:
        logger.warning("🎵 [TOOL] retrieve_audio_content: embedding model or database not available")
        return "Unable to process query - embedding model or database not available."
        
    try:
        logger.info(f"🎵 [TOOL] Searching {AUDIO_COLLECTION_NAME} collection...")
        audio_hits = qdrant_client.query_points(
            collection_name=AUDIO_COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=limit,
            with_payload=True
        )
        
        logger.info(f"🎵 [TOOL] Found {len(audio_hits.points)} audio hits")
        
        results = []
        for hit in audio_hits.points:
            payload = hit.payload or {}
            results.append({
                "score": hit.score,
                "speaker": payload.get("speaker_label"),
                "transcript": payload.get("transcript_text"),
                "start_time": payload.get("start_time_seconds")
            })
        
        result_json = json.dumps(results, indent=2)
        logger.info(f"🎵 [TOOL] retrieve_audio_content returning {len(results)} results")
        return result_json
    except Exception as e:
        logger.error(f"🎵 [TOOL] Error retrieving audio content: {e}")
        return f"Error retrieving audio content: {str(e)}"

@function_tool
def get_graph_relationships(entity_ids: List[str]) -> str:
    """Get entity relationships from graph database."""
    logger.info(f"🔗 [TOOL] get_graph_relationships called with entity_ids: {entity_ids}")
    
    neo4j_driver = get_neo4j_driver()
    if not neo4j_driver or not entity_ids:
        logger.warning("🔗 [TOOL] get_graph_relationships: no graph connection or entity IDs provided")
        return "No graph connection or entity IDs provided."
        
    try:
        logger.info(f"🔗 [TOOL] Querying Neo4j for relationships of {len(entity_ids)} entities...")
        with neo4j_driver.session() as session:
            query = """
            MATCH (e:Entity)-[r]-(other:Entity)
            WHERE e.entity_id IN $entity_ids
            RETURN e.entity_id, type(r), other.entity_id
            LIMIT 10
            """
            result = session.run(query, entity_ids=entity_ids)
            
            relationships = []
            for record in result:
                relationships.append(f"{record[0]} {record[1]} {record[2]}")
            
            result_text = "\n".join(relationships) if relationships else "No relationships found."
            logger.info(f"🔗 [TOOL] get_graph_relationships returning {len(relationships)} relationships")
            return result_text
    except Exception as e:
        logger.error(f"🔗 [TOOL] Error getting relationships: {e}")
        return f"Error: {str(e)}"

@function_tool
def execute_cypher_query(cypher: str) -> str:
    """Execute a custom Cypher query on the graph database."""
    neo4j_driver = get_neo4j_driver()
    if not neo4j_driver:
        return "No graph database connection available."
        
    try:
        with neo4j_driver.session() as session:
            result = session.run(cypher)
            
            records = []
            for record in result:
                records.append(dict(record))
            
            if not records:
                return "No results found."
            
            return json.dumps(records, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        return f"Error executing query: {str(e)}"

@function_tool
def get_dataset_statistics() -> str:
    """Get basic statistics about the stored data."""
    try:
        stats = {}
        
        # Qdrant collection stats
        qdrant_client = get_qdrant_client()
        if qdrant_client:
            collections = [ENTITY_COLLECTION_NAME, FRAME_COLLECTION_NAME, AUDIO_COLLECTION_NAME]
            for collection in collections:
                try:
                    info = qdrant_client.get_collection(collection)
                    stats[f"{collection}_count"] = info.points_count
                except:
                    stats[f"{collection}_count"] = 0
        
        # Neo4j stats
        neo4j_driver = get_neo4j_driver()
        if neo4j_driver:
            with neo4j_driver.session() as session:
                result = session.run("MATCH (n:Entity) RETURN count(n) as entity_count")
                record = result.single()
                stats["graph_entities"] = record["entity_count"] if record else 0
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                record = result.single()
                stats["graph_relationships"] = record["rel_count"] if record else 0
        
        return json.dumps(stats, indent=2)
    except Exception as e:
        logger.error(f"Error getting dataset statistics: {e}")
        return f"Error getting statistics: {str(e)}"

@function_tool
def retrieve_conversation_history(query: str, limit: int = 5) -> str:
    """Retrieve relevant conversation history from previous interactions."""
    logger.info(f"💭 [TOOL] retrieve_conversation_history called with query: '{query}', limit: {limit}")
    
    query_embedding = embed_text(query)
    qdrant_client = get_qdrant_client()
    if query_embedding is None or not qdrant_client:
        logger.warning("💭 [TOOL] retrieve_conversation_history: embedding model or database not available")
        return "Unable to process query - embedding model or database not available."
        
    try:
        # Check if conversation collection exists
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        logger.info(f"💭 [TOOL] Available collections: {collection_names}")
        
        if CONVERSATION_COLLECTION_NAME not in collection_names:
            logger.warning(f"💭 [TOOL] Conversation collection '{CONVERSATION_COLLECTION_NAME}' does not exist")
            return "No conversation history available yet."
        
        logger.info(f"💭 [TOOL] Searching {CONVERSATION_COLLECTION_NAME} collection...")
        conversation_hits = qdrant_client.query_points(
            collection_name=CONVERSATION_COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=limit,
            with_payload=True
        )
        
        logger.info(f"💭 [TOOL] Found {len(conversation_hits.points)} conversation hits")
        
        results = []
        for hit in conversation_hits.points:
            payload = hit.payload or {}
            results.append({
                "score": hit.score,
                "conversation_id": payload.get("conversation_id"),
                "user_query": payload.get("user_query"),
                "ai_response": payload.get("ai_response"),
                "timestamp": payload.get("timestamp")
            })
        
        result_text = json.dumps(results, indent=2) if results else "No relevant conversation history found."
        logger.info(f"💭 [TOOL] retrieve_conversation_history returning {len(results)} results")
        return result_text
    except Exception as e:
        logger.error(f"💭 [TOOL] Error retrieving conversation history: {e}")
        return f"Error retrieving conversation history: {str(e)}"

def store_conversation_turn(user_query: str, ai_response: str) -> bool:
    """Store a conversation turn in the vector database for future retrieval."""
    try:
        logger.info(f"💾 [STORE] Storing conversation - User: '{user_query[:50]}...', AI: '{ai_response[:50]}...'")
        
        # Check if qdrant_client is available
        qdrant_client = get_qdrant_client()
        if not qdrant_client:
            logger.error("💾 [STORE] Qdrant client not initialized - cannot store conversation turn")
            return False
        
        # Ensure conversation collection exists
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        logger.info(f"💾 [STORE] Available collections: {collection_names}")
        
        if CONVERSATION_COLLECTION_NAME not in collection_names:
            logger.info(f"💾 [STORE] Creating conversation collection: {CONVERSATION_COLLECTION_NAME}")
            # Get embedding dimension from existing collections
            embed_dim = 512  # Default for clip-ViT-B-32
            try:
                info = qdrant_client.get_collection(ENTITY_COLLECTION_NAME)
                embed_dim = info.config.params.vectors.size
                logger.info(f"💾 [STORE] Got embedding dimension from entities collection: {embed_dim}")
            except Exception as e:
                logger.warning(f"💾 [STORE] Could not get embedding dimension from entities: {e}, using default: {embed_dim}")
                
            qdrant_client.recreate_collection(
                collection_name=CONVERSATION_COLLECTION_NAME,
                vectors_config=models.VectorParams(size=embed_dim, distance=models.Distance.COSINE)
            )
            logger.info(f"💾 [STORE] Created conversation collection with dimension: {embed_dim}")
        
        # Create combined text for embedding
        conversation_text = f"User: {user_query}\nAssistant: {ai_response}"
        logger.info(f"💾 [STORE] Creating embedding for conversation text (length: {len(conversation_text)})")
        embedding = embed_text(conversation_text)
        
        if embedding is None:
            logger.error("💾 [STORE] Failed to create embedding for conversation text")
            return False
        
        logger.info(f"💾 [STORE] Created embedding with shape: {embedding.shape}")
        
        # Create unique ID for this conversation turn
        conversation_id = str(uuid.uuid4())
        logger.info(f"💾 [STORE] Generated conversation ID: {conversation_id}")
        
        # Store in Qdrant
        point = models.PointStruct(
            id=conversation_id,
            vector=embedding.tolist(),
            payload={
                "conversation_id": conversation_id,
                "user_query": user_query,
                "ai_response": ai_response,
                "timestamp": datetime.now().isoformat(),
                "conversation_text": conversation_text
            }
        )
        
        logger.info(f"💾 [STORE] Upserting point to collection: {CONVERSATION_COLLECTION_NAME}")
        qdrant_client.upsert(collection_name=CONVERSATION_COLLECTION_NAME, points=[point])
        logger.info(f"💾 [STORE] Successfully stored conversation turn: {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"💾 [STORE] Error storing conversation turn: {e}")
        import traceback
        logger.error(f"💾 [STORE] Traceback: {traceback.format_exc()}")
        return False 