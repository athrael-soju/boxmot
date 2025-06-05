"""
Multi-Agent Query Service using OpenAI Agents SDK

This replaces the previous infer.py with a sophisticated multi-agent system.
"""

import os
import argparse
import logging
import asyncio
import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

# OpenAI Agents SDK imports
from agents import Agent, Runner, function_tool
from agents.handoffs import Handoff

# Existing system imports
import openai
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
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
    
    # Initialize Qdrant
    qdrant_client = QdrantClient(host='localhost', port=6333)
    
    # Initialize Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j") 
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=basic_auth(neo4j_user, neo4j_password))
    
    # Initialize embedding model
    model_name = os.getenv("EMBEDDING_MODEL_NAME", "clip-ViT-B-32")
    embedding_model = SentenceTransformer(model_name, device='cpu')
    
    logger.info("All components initialized successfully.")

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

@function_tool
def retrieve_visual_content(query: str, limit: int = 5) -> str:
    """Retrieve visual content from vector database."""
    logger.info(f"🔍 [TOOL] retrieve_visual_content called with query: '{query}', limit: {limit}")
    
    query_embedding = embed_text(query)
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

# Additional tools for enhanced functionality
@function_tool
def execute_cypher_query(cypher: str) -> str:
    """Execute a custom Cypher query on the graph database."""
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
        if qdrant_client:
            collections = [ENTITY_COLLECTION_NAME, FRAME_COLLECTION_NAME, AUDIO_COLLECTION_NAME]
            for collection in collections:
                try:
                    info = qdrant_client.get_collection(collection)
                    stats[f"{collection}_count"] = info.points_count
                except:
                    stats[f"{collection}_count"] = 0
        
        # Neo4j stats
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

# Agent definitions
query_optimization_agent = Agent(
    name="Query Optimization Agent",
    instructions="""You are a query optimization specialist. Your role is to:
    
    1. Analyze user queries for clarity and specificity
    2. Identify if a query is too broad, unclear, or missing context
    3. Return either:
       - An optimized, more specific version of the query
       - A clarification request asking for more details
    
    If the query is already clear and specific, return it unchanged.
    If it needs optimization, provide a better version.
    If it's unclear, ask for clarification.
    
    Format your response as JSON with 'action' ('optimize', 'clarify', or 'pass_through') and 'result' fields."""
)

quick_answer_agent = Agent(
    name="Quick Answer Agent", 
    instructions="""You are a quick response specialist for general questions. Your role is to:
    
    1. Answer general questions that don't require access to the stored data
    2. Handle queries about system capabilities and features
    3. Provide helpful responses for common questions
    4. Identify when a query requires data access (return "NEEDS_DATA_ACCESS")
    
    You should handle:
    - General knowledge questions
    - Questions about the system's capabilities
    - Simple explanations and definitions
    - Greetings and basic interactions
    
    If the query requires accessing stored video, audio, or graph data, respond with exactly "NEEDS_DATA_ACCESS"."""
)

memory_agent = Agent(
    name="Memory Agent", 
    instructions="""You are a conversation memory specialist. Your role is to:
    
    1. Retrieve relevant information from previous conversations
    2. Provide context from past interactions
    3. Help maintain continuity across conversations
    4. Handle ALL queries about past conversations, conversation history, or "what was said before"
    
    IMPORTANT: You are the ONLY agent that handles conversation history queries.
    You also have access to dataset statistics for context when needed.
    
    Use the retrieve_conversation_history tool to find relevant past conversations.
    Summarize the relevant context for the current query.""",
    tools=[retrieve_conversation_history, get_dataset_statistics]
)

librarian_agent = Agent(
    name="Librarian Agent",
    instructions="""You are a data librarian with access to multimodal data including visual content, audio transcripts, and graph relationships. Your role is to:
    
    1. Retrieve and analyze visual content (images/captions) from video data
    2. Search through audio transcripts and diarization data
    3. Query graph relationships between entities
    4. Execute complex queries combining multiple data sources
    5. Provide accurate, detailed answers with specific data references
    
    Available data sources:
    - Visual content: detected entities and video frames with descriptions
    - Audio transcripts: speaker-diarized transcripts with timestamps
    - Graph data: entity relationships and interactions
    
    IMPORTANT: You do NOT handle queries about past conversations or conversation history. 
    Those should be routed to the Memory Agent.
    
    Always provide specific references to the data you retrieve (timestamps, entity IDs, etc.).
    If you need multiple queries to answer completely, execute them sequentially.
    
    Use the tools available to gather comprehensive information before providing your final answer.""",
    tools=[
        retrieve_visual_content,
        retrieve_audio_content, 
        get_graph_relationships,
        execute_cypher_query
    ]
)

secretary_agent = Agent(
    name="Secretary Agent",
    instructions="""You are the main coordinator for a multimodal query system. Your role is to:
    
    1. Analyze incoming user queries
    2. Route queries to the appropriate specialist agent
    3. Coordinate responses from multiple agents when needed
    
    Routing rules (in priority order):
    - For unclear or overly broad queries → Query Optimization Agent
    - For general questions not requiring data access → Quick Answer Agent
    - For queries about "past conversations", "conversation history", "what was said before", "previous interactions", "memory", or "recall" → Memory Agent
    - For queries requiring data retrieval from video, audio, or graph data → Librarian Agent
    
    CRITICAL: Queries containing words like "conversations", "history", "previous", "past", "recall", "remember", "said before" MUST go to Memory Agent.
    
    IMPORTANT: When you decide to hand off to another agent, you MUST first state clearly: "Routing to [Agent Name] because [reason]" before making the handoff.
    
    Always route to the most appropriate agent first. You can coordinate between agents as needed.""",
    handoffs=[query_optimization_agent, quick_answer_agent, memory_agent, librarian_agent]
)

class MultiAgentQueryService:
    """Main service for multi-agent queries."""
    
    def __init__(self):
        self.save_dir_base = Path("runs/track/exp/agents_infer")
        self.save_dir_base.mkdir(parents=True, exist_ok=True)
        
    async def process_query(self, user_query: str) -> str:
        """Process a query through the agent system."""
        try:
            # Create timestamped directory for this query
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            query_save_dir = self.save_dir_base / timestamp_str
            query_save_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"🤖 [QUERY] Processing query: {user_query[:100]}...")
            logger.info(f"🤖 [QUERY] Processing query: {user_query[:100]}...")
            
            # Run the query through the agent system
            print("📋 [AGENT_SYSTEM] Starting with Secretary Agent (Router)...")
            logger.info("📋 [AGENT_SYSTEM] Starting with Secretary Agent (Router)...")
            result = await Runner.run(secretary_agent, input=user_query)
            
            print(f"📋 [AGENT_SYSTEM] Got result type: {type(result)}")
            print(f"📋 [AGENT_SYSTEM] Result attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
            logger.info(f"📋 [AGENT_SYSTEM] Got result type: {type(result)}")
            
            # Enhanced agent routing analysis using available result attributes
            print(f"📋 [AGENT_SYSTEM] Analyzing agent routing...")
            logger.info(f"📋 [AGENT_SYSTEM] Analyzing agent routing...")
            
            # Check which agent handled the final response
            if hasattr(result, 'last_agent') and result.last_agent:
                print(f"🎯 [FINAL_AGENT] Last active agent: {result.last_agent.name}")
                logger.info(f"🎯 [FINAL_AGENT] Last active agent: {result.last_agent.name}")
            else:
                print(f"🎯 [FINAL_AGENT] No last_agent information available")
                logger.info(f"🎯 [FINAL_AGENT] No last_agent information available")
            
            # Analyze raw responses for conversation flow
            if hasattr(result, 'raw_responses') and result.raw_responses:
                print(f"📋 [AGENT_SYSTEM] Found {len(result.raw_responses)} raw responses")
                logger.info(f"📋 [AGENT_SYSTEM] Found {len(result.raw_responses)} raw responses")
                
                routing_decisions = []
                tool_calls_found = []
                
                for i, response in enumerate(result.raw_responses):
                    print(f"📋 [RESPONSE_TRACE] Response {i+1}: {str(response)[:200]}{'...' if len(str(response)) > 200 else ''}")
                    
                    response_str = str(response)
                    
                    # Look for routing decisions
                    if "Routing to" in response_str or "routing to" in response_str:
                        routing_decisions.append(response_str[:300])
                        print(f"🔄 [ROUTING] Decision found in response {i+1}: {response_str[:200]}{'...' if len(response_str) > 200 else ''}")
                        logger.info(f"🔄 [ROUTING] Decision found in response {i+1}: {response_str[:200]}{'...' if len(response_str) > 200 else ''}")
                    
                    # Look for tool calls to infer agent activity  
                    if "retrieve_conversation_history" in response_str:
                        tool_calls_found.append("Memory Agent (conversation history)")
                        print(f"🧠 [TOOL_DETECTED] Memory Agent tool call detected in response {i+1}")
                        logger.info(f"🧠 [TOOL_DETECTED] Memory Agent tool call detected in response {i+1}")
                    elif "retrieve_visual_content" in response_str or "retrieve_audio_content" in response_str:
                        tool_calls_found.append("Librarian Agent (data retrieval)")
                        print(f"📚 [TOOL_DETECTED] Librarian Agent tool call detected in response {i+1}")
                        logger.info(f"📚 [TOOL_DETECTED] Librarian Agent tool call detected in response {i+1}")
                    elif "get_graph_relationships" in response_str:
                        tool_calls_found.append("Librarian Agent (graph relationships)")
                        print(f"📚 [TOOL_DETECTED] Librarian Agent graph tool detected in response {i+1}")
                        logger.info(f"📚 [TOOL_DETECTED] Librarian Agent graph tool detected in response {i+1}")
                
                if routing_decisions:
                    print(f"🔄 [ROUTING_SUMMARY] Found {len(routing_decisions)} routing decisions")
                    logger.info(f"🔄 [ROUTING_SUMMARY] Found {len(routing_decisions)} routing decisions")
                
                if tool_calls_found:
                    print(f"🛠️ [TOOLS_SUMMARY] Tools called: {', '.join(set(tool_calls_found))}")
                    logger.info(f"🛠️ [TOOLS_SUMMARY] Tools called: {', '.join(set(tool_calls_found))}")
                else:
                    print(f"🛠️ [TOOLS_SUMMARY] No agent tool calls detected")
                    logger.info(f"🛠️ [TOOLS_SUMMARY] No agent tool calls detected")
            else:
                print(f"📋 [AGENT_SYSTEM] No raw_responses available for analysis")
                logger.info(f"📋 [AGENT_SYSTEM] No raw_responses available for analysis")
            
            ai_response = result.final_output
            print(f"✅ [RESPONSE] Final response ({len(ai_response)} chars): {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")
            logger.info(f"✅ [RESPONSE] Final response ({len(ai_response)} chars): {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")
            
            # Try to infer final handling agent from response content
            if "conversation" in ai_response.lower() and ("history" in ai_response.lower() or "found" in ai_response.lower()):
                print(f"🧠 [FINAL_AGENT] Response suggests Memory Agent handled the query")
                logger.info(f"🧠 [FINAL_AGENT] Response suggests Memory Agent handled the query")
            elif any(keyword in ai_response.lower() for keyword in ["visual", "audio", "entity", "frame", "found", "retrieved"]):
                print(f"📚 [FINAL_AGENT] Response suggests Librarian Agent handled the query")
                logger.info(f"📚 [FINAL_AGENT] Response suggests Librarian Agent handled the query")
            elif len(ai_response) < 200 and any(keyword in ai_response.lower() for keyword in ["hello", "help", "i can", "assistance"]):
                print(f"⚡ [FINAL_AGENT] Response suggests Quick Answer Agent handled the query")
                logger.info(f"⚡ [FINAL_AGENT] Response suggests Quick Answer Agent handled the query")
            else:
                print(f"❓ [FINAL_AGENT] Could not determine final handling agent from response")
                logger.info(f"❓ [FINAL_AGENT] Could not determine final handling agent from response")
            
            # Store the conversation turn for future reference
            logger.info("💾 [STORAGE] Storing conversation turn...")
            success = store_conversation_turn(user_query, ai_response)
            if success:
                logger.info("💾 [STORAGE] Successfully stored conversation turn")
            else:
                logger.warning("💾 [STORAGE] Failed to store conversation turn")
            
            # Save interaction log with enhanced agent tracking
            interaction_log = {
                "timestamp": datetime.now().isoformat(),
                "user_query": user_query,
                "ai_response": ai_response,
                "agent_traces": [str(msg) for msg in result.messages] if hasattr(result, 'messages') else [],
                "conversation_flow": len(result.messages) if hasattr(result, 'messages') else 0
            }
            
            log_file_path = query_save_dir / "interaction_log.json"
            with open(log_file_path, 'w') as f:
                json.dump(interaction_log, f, indent=2)
            
            logger.info(f"📄 [LOG] Query processed. Log saved to: {log_file_path}")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ [ERROR] Error processing query: {e}")
            import traceback
            logger.error(f"❌ [ERROR] Traceback: {traceback.format_exc()}")
            return f"I apologize, but I encountered an error processing your query: {str(e)}"
    
    async def interactive_loop(self):
        """Run interactive query loop."""
        logger.info("Starting interactive multi-agent query service. Type 'exit' or 'quit' to end.")
        print("🤖 Multi-Agent Query Service")
        print("=" * 50)
        print("Available agents:")
        print("  📋 Secretary Agent - Routes your queries")
        print("  🔍 Query Optimization Agent - Clarifies unclear queries")
        print("  ⚡ Quick Answer Agent - Handles general questions")
        print("  📚 Memory Agent - Recalls past conversations") 
        print("  📖 Librarian Agent - Searches multimodal data")
        print("=" * 50)
        print("Type 'exit' or 'quit' to end, or ask any question!")
        
        while True:
            try:
                user_query = input("\n🧑 You: ").strip()
                if user_query.lower() in ["exit", "quit"]:
                    logger.info("Exiting interactive loop.")
                    print("👋 Goodbye!")
                    break
                if not user_query:
                    continue
                
                print("🤖 Assistant: ", end="")
                response = await self.process_query(user_query)
                print(response)
                
            except KeyboardInterrupt:
                logger.info("\nUser interrupted (Ctrl+C). Exiting interactive loop.")
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error in interactive loop: {e}")
                print(f"❌ Sorry, I encountered an error: {str(e)}")

async def main():
    """Main function to run the multi-agent query service."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Query Service for Multimodal Data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Database connection arguments
    parser.add_argument(
        "--neo4j-uri", type=str, default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j URI. Can also be set via NEO4J_URI environment variable.",
    )
    parser.add_argument(
        "--neo4j-user", type=str, default=os.environ.get("NEO4J_USER", "neo4j"),
        help="Neo4j username. Can also be set via NEO4J_USER environment variable.",
    )
    parser.add_argument(
        "--neo4j-pass", type=str, dest="neo4j_password", default=os.environ.get("NEO4J_PASSWORD", "password"),
        help="Neo4j password. Can also be set via NEO4J_PASSWORD environment variable.",
    )
    parser.add_argument(
        "--qdrant-host", type=str, default=os.environ.get("QDRANT_HOST", "localhost"),
        help="Qdrant host. Can also be set via QDRANT_HOST environment variable.",
    )
    parser.add_argument(
        "--qdrant-port", type=int, default=int(os.environ.get("QDRANT_PORT", 6333)),
        help="Qdrant port. Can also be set via QDRANT_PORT environment variable.",
    )
    
    # Processing arguments
    parser.add_argument(
        "--embedding-model", type=str, default=os.environ.get("EMBEDDING_MODEL_NAME", "clip-ViT-B-32"),
        help="Embedding model to use for text/image encoding.",
    )
    parser.add_argument(
        "--openai-model", type=str, default=os.environ.get("OPENAI_MODEL", "gpt-4_1-mini-2025-04-14"),
        help="OpenAI model to use for agent conversations.",
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        logger.info("🚀 Initializing multi-agent query service...")
        initialize_components()
        logger.info("✅ All components initialized successfully.")
        
        service = MultiAgentQueryService()
        await service.interactive_loop()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.critical(f"❌ Application failed to start: {e}")
    finally:
        if neo4j_driver:
            try:
                neo4j_driver.close()
                logger.info("Neo4j connection closed.")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
        logger.info("Application shutdown complete.")

if __name__ == "__main__":
    # Ensure OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required!")
        print("Please set it with: export OPENAI_API_KEY=your_api_key_here")
        exit(1)
    
    asyncio.run(main()) 