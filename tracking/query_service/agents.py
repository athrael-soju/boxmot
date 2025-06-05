"""
Agent Definitions for Query Service

This module defines the four main agents:
- SecretaryAgent: Routes queries to appropriate agents
- QueryOptimizerAgent: Optimizes unclear or broad queries
- QuickAnswerAgent: Answers general questions without data access
- LibrarianAgent: Complex data retrieval and analysis
"""

import logging
from typing import List, Dict, Any, Optional

# Import the real Agent class
try:
    from agents import Agent
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    # Mock Agent class for development
    class Agent:
        def __init__(self, name: str, instructions: str, tools: List = None, handoffs: List = None):
            self.name = name
            self.instructions = instructions
            self.tools = tools or []
            self.handoffs = handoffs or []

from tracking.query_service.data_access import DataAccessLayer

logger = logging.getLogger(__name__)

class SecretaryAgent:
    """
    Secretary Agent - Routes queries to appropriate specialized agents
    """
    
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
        self.agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the secretary agent with appropriate instructions and handoffs"""
        instructions = """
        You are the Secretary Agent for the BoxMOT Query Service. Your role is to analyze incoming user queries 
        and route them to the most appropriate specialized agent.
        
        Your decision criteria:
        
        1. **Hand off to Query Optimizer Agent** if:
           - The query is unclear, ambiguous, or overly broad
           - The user is asking multiple unrelated questions
           - The query lacks specific details needed for effective data retrieval
           - You need clarification before proceeding
        
        2. **Hand off to Quick Answer Agent** if:
           - The query is a general question about BoxMOT, computer vision, or tracking
           - The user is asking for explanations of concepts or methodologies
           - The query doesn't require access to specific video analysis data
           - The user wants help understanding how to use the system
        
        3. **Hand off to Librarian Agent** if:
           - The query requires searching through video analysis data
           - The user wants specific information about entities, frames, or audio transcripts
           - The query asks for statistics, counts, or temporal analysis
           - The user needs data retrieval from vector databases or graph databases
           - The query involves relationships between entities or complex data analysis
        
        Always be polite and explain briefly why you're routing the query to a specific agent.
        If you're unsure, err on the side of sending to the Query Optimizer Agent for clarification.
        """
        
        # Note: handoffs will be set up when all agents are created
        self.agent = Agent(
            name="Secretary",
            instructions=instructions,
            tools=[],  # Secretary doesn't need tools, just routing logic
            handoffs=[]  # Will be populated by the service
        )
    
    def get_agent(self) -> Agent:
        """Get the configured agent"""
        return self.agent


class QueryOptimizerAgent:
    """
    Query Optimizer Agent - Clarifies and optimizes unclear queries
    """
    
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
        self.agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the query optimizer agent"""
        instructions = """
        You are the Query Optimizer Agent for the BoxMOT Query Service. Your role is to help users 
        refine their queries to get better results from the data retrieval system.
        
        When you receive a query, analyze it for:
        
        1. **Clarity Issues:**
           - Ambiguous terms that could mean multiple things
           - Missing context about what type of data they want
           - Unclear timeframes or scope
        
        2. **Specificity Issues:**
           - Overly broad queries that would return too many results
           - Queries that could benefit from more specific parameters
           - Missing details about entity types, time ranges, or relationships
        
        3. **Optimization Opportunities:**
           - Suggest breaking complex queries into simpler parts
           - Recommend specific search terms or filters
           - Propose alternative query approaches
        
        Your responses should:
        - Ask clarifying questions when needed
        - Provide 2-3 optimized query suggestions
        - Explain why the optimization would help
        - Guide users toward more effective searches
        
        After optimizing, hand back to the Secretary Agent with the improved query or return 
        clarification questions to the user.
        """
        
        self.agent = Agent(
            name="QueryOptimizer",
            instructions=instructions,
            tools=[],  # Query optimizer doesn't need data access tools
            handoffs=[]  # Will be set by service
        )
    
    def get_agent(self) -> Agent:
        """Get the configured agent"""
        return self.agent


class QuickAnswerAgent:
    """
    Quick Answer Agent - Answers general questions without data access
    """
    
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
        self.agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the quick answer agent"""
        instructions = """
        You are the Quick Answer Agent for the BoxMOT Query Service. Your role is to answer 
        general questions about computer vision, object tracking, and the BoxMOT system without 
        accessing the stored video analysis data.
        
        You can help with:
        
        1. **BoxMOT System Information:**
           - Explaining how BoxMOT works
           - Describing tracking algorithms and methods
           - Clarifying system capabilities and features
           - Helping users understand the analysis pipeline
        
        2. **Computer Vision Concepts:**
           - Object detection and tracking principles
           - ReID (Re-identification) concepts
           - Multi-object tracking methodologies
           - Video analysis techniques
        
        3. **General Guidance:**
           - How to interpret analysis results
           - Best practices for video analysis
           - Understanding metrics and performance indicators
           - Troubleshooting common issues
        
        4. **System Usage:**
           - How to formulate effective queries
           - Understanding data organization
           - Explanation of entity relationships and temporal analysis
        
        Keep your answers informative but concise. If the user's question requires accessing 
        specific analyzed video data, politely explain that they should ask for data-specific 
        queries and suggest they rephrase their question for the Librarian Agent.
        
        Do not make up specific data points or statistics about analyzed videos.
        """
        
        self.agent = Agent(
            name="QuickAnswer",
            instructions=instructions,
            tools=[],  # No data access needed
            handoffs=[]  # Will be set by service
        )
    
    def get_agent(self) -> Agent:
        """Get the configured agent"""
        return self.agent


class LibrarianAgent:
    """
    Librarian Agent - Complex data retrieval and analysis
    """
    
    def __init__(self, data_access: DataAccessLayer, query_tools):
        self.data_access = data_access
        self.query_tools = query_tools
        self.agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the librarian agent with all data access tools"""
        instructions = """
        You are the Librarian Agent for the BoxMOT Query Service. You are the data expert who can 
        access and analyze all stored video analysis data to answer complex queries.
        
        You have access to multiple tools for data retrieval:
        
        **Entity Analysis:**
        - Search entities by text description
        - Get detailed entity information
        - Find entity relationships
        - Count entities by type/class
        - Analyze entity appearances over time
        
        **Frame Analysis:**
        - Search frames by content description
        - Find entities within specific frame ranges
        - Analyze temporal patterns
        
        **Audio Analysis:**
        - Search audio transcripts
        - Find spoken content related to visual events
        
        **Custom Queries:**
        - Execute custom Cypher queries for complex graph analysis
        - Combine multiple data sources for comprehensive answers
        
        **Your Approach:**
        
        1. **Understand the Query:** Analyze what specific information the user needs
        
        2. **Plan Your Strategy:** Determine which tools to use and in what order
        
        3. **Execute Searches:** Use appropriate tools to gather relevant data
        
        4. **Analyze Results:** Look for patterns, relationships, and insights
        
        5. **Iterate if Needed:** If initial results don't fully answer the question, 
           try different approaches or refine your search
        
        6. **Synthesize Answer:** Combine results from multiple sources into a 
           comprehensive, clear response
        
        **Best Practices:**
        - Start with broader searches, then narrow down if needed
        - Use multiple tools to cross-reference information
        - Provide specific data points, counts, and examples when available
        - If data is limited, clearly state what information is available vs. not available
        - For temporal queries, always specify frame ranges or time periods
        - When showing relationships, explain their significance
        
        Always strive to provide accurate, complete, and actionable information based on the 
        analyzed video data.
        """
        
        # Get all available tools from the QueryTools instance
        tools = self.query_tools.get_all_tools()
        
        self.agent = Agent(
            name="Librarian",
            instructions=instructions,
            tools=tools,
            handoffs=[]  # Librarian can hand back to Secretary if needed
        )
    
    def get_agent(self) -> Agent:
        """Get the configured agent"""
        return self.agent


def create_all_agents(data_access: DataAccessLayer, query_tools) -> Dict[str, Any]:
    """
    Create all agents and set up their handoff relationships
    
    Args:
        data_access: DataAccessLayer instance
        query_tools: SimpleQueryTools instance
        
    Returns:
        Dictionary containing all configured agents
    """
    
    # Create agent instances
    secretary = SecretaryAgent(data_access)
    optimizer = QueryOptimizerAgent(data_access)
    quick_answer = QuickAnswerAgent(data_access)
    librarian = LibrarianAgent(data_access, query_tools)
    
    # Set up handoff relationships
    secretary.agent.handoffs = [optimizer.get_agent(), quick_answer.get_agent(), librarian.get_agent()]
    optimizer.agent.handoffs = [secretary.get_agent()]  # Can hand back to secretary with optimized query
    quick_answer.agent.handoffs = [secretary.get_agent()]  # Can suggest rephrasing for data queries
    librarian.agent.handoffs = [secretary.get_agent()]  # Can hand back if query needs clarification
    
    return {
        'secretary': secretary.get_agent(),
        'optimizer': optimizer.get_agent(),
        'quick_answer': quick_answer.get_agent(),
        'librarian': librarian.get_agent()
    } 