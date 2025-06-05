#!/usr/bin/env python3
"""Test script to specifically test the Librarian Agent and its tools."""

import asyncio
import os
import logging
from pathlib import Path
import sys

# Add tracking directory to path
sys.path.append(str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import agent components
from agents_infer import (
    initialize_components, 
    librarian_agent,
    embed_text,
    qdrant_client,
    neo4j_driver,
    ENTITY_COLLECTION_NAME,
    FRAME_COLLECTION_NAME,
    AUDIO_COLLECTION_NAME,
    CONVERSATION_COLLECTION_NAME
)

# Import the Runner for OpenAI agents
from agents import Runner

import json
import uuid
from datetime import datetime

def test_retrieve_visual_content_direct(query: str, limit: int = 5) -> str:
    """Direct test of visual content retrieval without function_tool wrapper."""
    logger.info(f"🔍 [DIRECT_TOOL] retrieve_visual_content called with query: '{query}', limit: {limit}")
    
    query_embedding = embed_text(query)
    if query_embedding is None or not qdrant_client:
        logger.warning("🔍 [DIRECT_TOOL] retrieve_visual_content: embedding model or database not available")
        return "Unable to process query - embedding model or database not available."
    
    try:
        logger.info(f"🔍 [DIRECT_TOOL] Searching {ENTITY_COLLECTION_NAME} collection...")
        # Search entities
        entity_hits = qdrant_client.query_points(
            collection_name=ENTITY_COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=limit,
            with_payload=True
        )
        
        logger.info(f"🔍 [DIRECT_TOOL] Found {len(entity_hits.points)} entity hits")
        
        results = []
        for hit in entity_hits.points:
            payload = hit.payload or {}
            results.append({
                "type": "entity",
                "score": hit.score,
                "entity_id": payload.get("entity_id"),
                "class_name": payload.get("class_name"),
                "caption": payload.get("image_caption", "No caption available")
            })
        
        result_json = json.dumps(results, indent=2)
        logger.info(f"🔍 [DIRECT_TOOL] retrieve_visual_content returning {len(results)} results")
        return result_json
    except Exception as e:
        logger.error(f"🔍 [DIRECT_TOOL] Error retrieving visual content: {e}")
        return f"Error retrieving visual content: {str(e)}"

def test_get_dataset_statistics_direct() -> str:
    """Direct test of dataset statistics without function_tool wrapper."""
    logger.info("📊 [DIRECT_TOOL] get_dataset_statistics called")
    
    try:
        stats = {}
        
        # Qdrant collection stats
        if qdrant_client:
            collections = [ENTITY_COLLECTION_NAME, FRAME_COLLECTION_NAME, AUDIO_COLLECTION_NAME, CONVERSATION_COLLECTION_NAME]
            for collection in collections:
                try:
                    info = qdrant_client.get_collection(collection)
                    stats[f"{collection}_count"] = info.points_count
                    logger.info(f"📊 [DIRECT_TOOL] Collection {collection}: {info.points_count} points")
                except Exception as e:
                    stats[f"{collection}_count"] = 0
                    logger.warning(f"📊 [DIRECT_TOOL] Collection {collection} not found or error: {e}")
        
        # Neo4j stats
        if neo4j_driver:
            try:
                with neo4j_driver.session() as session:
                    result = session.run("MATCH (n:Entity) RETURN count(n) as entity_count")
                    record = result.single()
                    stats["graph_entities"] = record["entity_count"] if record else 0
                    
                    result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                    record = result.single()
                    stats["graph_relationships"] = record["rel_count"] if record else 0
                    
                    logger.info(f"📊 [DIRECT_TOOL] Neo4j entities: {stats['graph_entities']}, relationships: {stats['graph_relationships']}")
            except Exception as e:
                logger.warning(f"📊 [DIRECT_TOOL] Neo4j error: {e}")
                stats["graph_entities"] = "error"
                stats["graph_relationships"] = "error"
        else:
            stats["graph_entities"] = "no_connection"
            stats["graph_relationships"] = "no_connection"
        
        result_json = json.dumps(stats, indent=2)
        logger.info(f"📊 [DIRECT_TOOL] get_dataset_statistics returning stats")
        return result_json
    except Exception as e:
        logger.error(f"📊 [DIRECT_TOOL] Error getting dataset statistics: {e}")
        return f"Error getting statistics: {str(e)}"

def test_retrieve_conversation_history_direct(query: str, limit: int = 5) -> str:
    """Direct test of conversation history retrieval without function_tool wrapper."""
    logger.info(f"💭 [DIRECT_TOOL] retrieve_conversation_history called with query: '{query}', limit: {limit}")
    
    query_embedding = embed_text(query)
    if query_embedding is None or not qdrant_client:
        logger.warning("💭 [DIRECT_TOOL] retrieve_conversation_history: embedding model or database not available")
        return "Unable to process query - embedding model or database not available."
        
    try:
        # Check if conversation collection exists
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        logger.info(f"💭 [DIRECT_TOOL] Available collections: {collection_names}")
        
        if CONVERSATION_COLLECTION_NAME not in collection_names:
            logger.warning(f"💭 [DIRECT_TOOL] Conversation collection '{CONVERSATION_COLLECTION_NAME}' does not exist")
            return "No conversation history available yet."
        
        logger.info(f"💭 [DIRECT_TOOL] Searching {CONVERSATION_COLLECTION_NAME} collection...")
        conversation_hits = qdrant_client.query_points(
            collection_name=CONVERSATION_COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=limit,
            with_payload=True
        )
        
        logger.info(f"💭 [DIRECT_TOOL] Found {len(conversation_hits.points)} conversation hits")
        
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
        logger.info(f"💭 [DIRECT_TOOL] retrieve_conversation_history returning {len(results)} results")
        return result_text
    except Exception as e:
        logger.error(f"💭 [DIRECT_TOOL] Error retrieving conversation history: {e}")
        return f"Error retrieving conversation history: {str(e)}"

async def test_librarian_with_runner():
    """Test the librarian agent using the Runner framework."""
    
    # Initialize components
    logger.info("🚀 Initializing components...")
    initialize_components()
    logger.info("✅ Components initialized")
    
    # Test queries that should trigger different tools
    test_queries = [
        "show me visual content about a pink dress",
        "get dataset statistics",
        "find previous conversations about shoplifting"
    ]
    
    for query in test_queries:
        logger.info(f"\n🧪 TESTING LIBRARIAN AGENT WITH QUERY: '{query}'")
        logger.info("=" * 60)
        
        try:
            # Run query through librarian agent using Runner
            result = await Runner.run(librarian_agent, input=query)
            
            # Extract response
            response = result.final_output
            logger.info(f"📝 AGENT RESPONSE: {response[:300]}{'...' if len(response) > 300 else ''}")
            
        except Exception as e:
            logger.error(f"❌ AGENT ERROR: {e}")
            import traceback
            logger.error(f"❌ AGENT TRACEBACK: {traceback.format_exc()}")
        
        logger.info("=" * 60)

async def test_tools_directly():
    """Test the tools directly to see if they work."""
    
    logger.info("\n🔧 TESTING TOOLS DIRECTLY")
    logger.info("=" * 60)
    
    # Initialize components
    initialize_components()
    
    # Test each tool
    try:
        logger.info("🧪 Testing retrieve_visual_content...")
        result1 = test_retrieve_visual_content_direct("pink dress", 3)
        logger.info(f"📝 Visual content result: {result1[:200]}{'...' if len(result1) > 200 else ''}")
    except Exception as e:
        logger.error(f"❌ Visual content error: {e}")
    
    try:
        logger.info("🧪 Testing get_dataset_statistics...")
        result2 = test_get_dataset_statistics_direct()
        logger.info(f"📝 Dataset stats result: {result2[:200]}{'...' if len(result2) > 200 else ''}")
    except Exception as e:
        logger.error(f"❌ Dataset stats error: {e}")
    
    try:
        logger.info("🧪 Testing retrieve_conversation_history...")
        result3 = test_retrieve_conversation_history_direct("shoplifting", 3)
        logger.info(f"📝 Conversation history result: {result3[:200]}{'...' if len(result3) > 200 else ''}")
    except Exception as e:
        logger.error(f"❌ Conversation history error: {e}")

async def main():
    """Main test function."""
    logger.info("🚀 Starting Librarian Agent Test")
    
    # Test tools directly first
    await test_tools_directly()
    
    # Then test through the agent system
    await test_librarian_with_runner()
    
    logger.info("✅ Test completed")

if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required!")
        exit(1)
    
    asyncio.run(main()) 