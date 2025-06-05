"""
Main Query Service

This module contains the QueryService class that orchestrates all agents
and provides the main interface for the query system.
"""

import logging
import asyncio
import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# OpenAI Agents SDK imports
try:
    from agents import Runner
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    # Mock classes for development
    class Runner:
        @staticmethod
        async def run(starting_agent, input: str, max_turns: int = 10, **kwargs):
            return type('MockResult', (), {
                'final_output': f"Mock response to: {input}",
                'agent_name': starting_agent.name if hasattr(starting_agent, 'name') else 'MockAgent'
            })()
        
        @staticmethod
        def run_sync(starting_agent, input: str, max_turns: int = 10, **kwargs):
            return type('MockResult', (), {
                'final_output': f"Mock response to: {input}",
                'agent_name': starting_agent.name if hasattr(starting_agent, 'name') else 'MockAgent'
            })()

# Import the correct model class
try:
    from agents import OpenAIChatCompletionsModel as ChatCompletionModel
except ImportError:
    # Create a mock ChatCompletionModel
    class ChatCompletionModel:
        def __init__(self, model: str):
            self.model = model

from .config import QueryServiceConfig
from .data_access import DataAccessLayer
from .simple_tools import SimpleQueryTools
from .query_agents import create_all_agents

logger = logging.getLogger(__name__)

class QueryService:
    """
    Main Query Service that coordinates all agents and provides query functionality
    """
    
    def __init__(self, config: Optional[QueryServiceConfig] = None):
        """
        Initialize the Query Service
        
        Args:
            config: Configuration object, if None will create with defaults
        """
        self.config = config or QueryServiceConfig()
        self.config.validate()
        
        # Initialize components
        self.data_access: Optional[DataAccessLayer] = None
        self.query_tools: Optional[SimpleQueryTools] = None
        self.agents: Dict[str, Any] = {}
        self.secretary_agent = None
        
        # Initialize service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize all service components"""
        try:
            logger.info("Initializing Query Service...")
            
            # Initialize data access layer
            logger.info("Setting up data access layer...")
            self.data_access = DataAccessLayer(self.config)
            
            # Initialize query tools
            logger.info("Setting up query tools...")
            self.query_tools = SimpleQueryTools(self.data_access)
            
            # Create all agents
            logger.info("Creating and configuring agents...")
            self.agents = create_all_agents(self.data_access, self.query_tools)
            self.secretary_agent = self.agents['secretary']
            
            logger.info("Query Service initialized successfully")
            logger.info(f"Available agents: {list(self.agents.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Query Service: {e}")
            raise
    
    async def query_async(self, user_input: str, save_logs: bool = True) -> Dict[str, Any]:
        """
        Process a query asynchronously
        
        Args:
            user_input: The user's query
            save_logs: Whether to save interaction logs
            
        Returns:
            Dictionary containing the response and metadata
        """
        query_start_time = datetime.datetime.now()
        query_id = f"query_{query_start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        logger.info(f"Processing query {query_id}: {user_input[:100]}...")
        
        try:
            # Run the query through the agent system starting with the secretary
            result = await Runner.run(
                starting_agent=self.secretary_agent,
                input=user_input,
                max_turns=self.config.max_query_iterations
            )
            
            query_end_time = datetime.datetime.now()
            processing_time = (query_end_time - query_start_time).total_seconds()
            
            response_data = {
                "query_id": query_id,
                "user_input": user_input,
                "response": result.final_output,
                "agent_used": getattr(result, 'agent_name', 'Unknown'),
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": query_start_time.isoformat(),
                "status": "success"
            }
            
            logger.info(f"Query {query_id} completed successfully in {processing_time:.3f}s")
            
            if save_logs:
                self._save_query_log(response_data)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing query {query_id}: {e}")
            query_end_time = datetime.datetime.now()
            processing_time = (query_end_time - query_start_time).total_seconds()
            
            error_response = {
                "query_id": query_id,
                "user_input": user_input,
                "error": str(e),
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": query_start_time.isoformat(),
                "status": "error"
            }
            
            if save_logs:
                self._save_query_log(error_response)
            
            return error_response
    
    def query_sync(self, user_input: str, save_logs: bool = True) -> Dict[str, Any]:
        """
        Process a query synchronously
        
        Args:
            user_input: The user's query
            save_logs: Whether to save interaction logs
            
        Returns:
            Dictionary containing the response and metadata
        """
        query_start_time = datetime.datetime.now()
        query_id = f"query_{query_start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        logger.info(f"Processing query {query_id}: {user_input[:100]}...")
        
        try:
            # Run the query through the agent system starting with the secretary
            result = Runner.run_sync(
                starting_agent=self.secretary_agent,
                input=user_input,
                max_turns=self.config.max_query_iterations
            )
            
            query_end_time = datetime.datetime.now()
            processing_time = (query_end_time - query_start_time).total_seconds()
            
            response_data = {
                "query_id": query_id,
                "user_input": user_input,
                "response": result.final_output,
                "agent_used": getattr(result, 'agent_name', 'Unknown'),
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": query_start_time.isoformat(),
                "status": "success"
            }
            
            logger.info(f"Query {query_id} completed successfully in {processing_time:.3f}s")
            
            if save_logs:
                self._save_query_log(response_data)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing query {query_id}: {e}")
            query_end_time = datetime.datetime.now()
            processing_time = (query_end_time - query_start_time).total_seconds()
            
            error_response = {
                "query_id": query_id,
                "user_input": user_input,
                "error": str(e),
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": query_start_time.isoformat(),
                "status": "error"
            }
            
            if save_logs:
                self._save_query_log(error_response)
            
            return error_response
    
    def _save_query_log(self, query_data: Dict[str, Any]):
        """Save query log to file"""
        try:
            # Create logs directory
            logs_dir = Path("runs/query_service/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Save individual query log
            query_id = query_data.get("query_id", "unknown")
            log_file = logs_dir / f"{query_id}.json"
            
            with open(log_file, 'w') as f:
                json.dump(query_data, f, indent=2)
            
            logger.debug(f"Query log saved to: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save query log: {e}")
    
    async def interactive_session(self):
        """
        Start an interactive query session
        """
        print("\n" + "="*60)
        print("      BoxMOT Query Service - Interactive Session")
        print("="*60)
        print("Ask questions about your video analysis data!")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("Type 'help' for guidance on query types.")
        print("-"*60)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nThank you for using BoxMOT Query Service!")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                if not user_input:
                    continue
                
                print("Processing your query...")
                
                # Process the query
                result = await self.query_async(user_input)
                
                if result["status"] == "success":
                    print(f"\nAssistant: {result['response']}")
                else:
                    print(f"\nError: {result.get('error', 'Unknown error occurred')}")
                
            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error in interactive session: {e}")
                print(f"\nAn error occurred: {e}")
    
    def _show_help(self):
        """Show help information for the interactive session"""
        help_text = """
Query Examples:

📊 Data Analysis:
  • "How many people appear in the video?"
  • "What entities appear most frequently?"
  • "Show me all cars in frames 100-200"

🔍 Search Queries:
  • "Find frames with people walking"
  • "Search for audio mentioning 'car'"
  • "Show me entities related to person_1"

⏱️ Temporal Analysis:
  • "When does entity_5 first appear?"
  • "What happens between frames 50 and 100?"
  • "Analyze entity appearances over time"

💬 Audio Analysis:
  • "What was said about the red car?"
  • "Find audio segments from speaker S1"
  • "Search transcripts for 'important meeting'"

❓ General Questions:
  • "How does BoxMOT tracking work?"
  • "What is ReID in computer vision?"
  • "Explain entity relationships"

The system will automatically route your query to the most appropriate agent!
        """
        print(help_text)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and statistics
        
        Returns:
            Dictionary containing system status information
        """
        try:
            status = {
                "service_status": "running",
                "agents_available": list(self.agents.keys()),
                "data_access_status": "connected" if self.data_access else "disconnected",
                "config": {
                    "model": self.config.openai_model,
                    "max_iterations": self.config.max_query_iterations,
                    "similarity_threshold": self.config.similarity_threshold
                }
            }
            
            # Test data connections
            if self.data_access:
                try:
                    # Test basic connectivity
                    entity_counts = self.data_access.count_entities_by_class()
                    status["data_statistics"] = {
                        "total_entity_types": len(entity_counts),
                        "entity_counts": entity_counts
                    }
                except Exception as e:
                    status["data_access_error"] = str(e)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "service_status": "error",
                "error": str(e)
            }
    
    def close(self):
        """Clean up resources"""
        try:
            if self.data_access:
                self.data_access.close()
            logger.info("Query Service closed successfully")
        except Exception as e:
            logger.error(f"Error closing Query Service: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close() 