"""
Main service class for the multi-agent query service.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from agents import Runner

from .agents.secretary import secretary_agent
from .tools import store_conversation_turn
from .core import logger

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
            
            # Run enhanced intent analysis
            from .intent_classifier import intent_classifier
            intent_analysis = intent_classifier.get_routing_recommendation(user_query)
            print(f"🧠 [INTENT] {intent_analysis['reasoning']}")
            print(f"🎯 [INTENT] Recommended: {intent_analysis['recommended_agent']} (confidence: {intent_analysis['confidence']:.2f})")
            logger.info(f"🧠 [INTENT] {intent_analysis['reasoning']}")
            logger.info(f"🎯 [INTENT] Recommended: {intent_analysis['recommended_agent']} (confidence: {intent_analysis['confidence']:.2f})")
            
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