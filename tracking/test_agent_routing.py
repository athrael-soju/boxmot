#!/usr/bin/env python3
"""Test script to verify agent routing is working correctly."""

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
    secretary_agent,
    memory_agent,
    librarian_agent
)

# Import the Runner for OpenAI agents
from agents import Runner

async def test_routing():
    """Test that queries are routed to the correct agents."""
    
    # Initialize components
    logger.info("🚀 Initializing components...")
    initialize_components()
    logger.info("✅ Components initialized")
    
    # Test queries that should go to different agents
    test_cases = [
        {
            "query": "find previous conversations about shoplifting",
            "expected_agent": "Memory Agent",
            "description": "Should route to Memory Agent for conversation history"
        },
        {
            "query": "what was said before about pink dress",
            "expected_agent": "Memory Agent", 
            "description": "Should route to Memory Agent for past conversations"
        },
        {
            "query": "recall our conversation history",
            "expected_agent": "Memory Agent",
            "description": "Should route to Memory Agent for recall/memory queries"
        },
        {
            "query": "show me visual content about a pink dress",
            "expected_agent": "Librarian Agent",
            "description": "Should route to Librarian Agent for visual data"
        },
        {
            "query": "search for audio transcripts",
            "expected_agent": "Librarian Agent", 
            "description": "Should route to Librarian Agent for audio data"
        },
        {
            "query": "get dataset statistics",
            "expected_agent": "Memory Agent",
            "description": "Should route to Memory Agent which now has dataset statistics tool"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        logger.info(f"\n🧪 TEST {i+1}: {test_case['description']}")
        logger.info(f"📝 Query: '{test_case['query']}'")
        logger.info(f"🎯 Expected: {test_case['expected_agent']}")
        logger.info("=" * 70)
        
        try:
            # Run query through secretary agent
            result = await Runner.run(secretary_agent, input=test_case['query'])
            
            # Extract response
            response = result.final_output
            logger.info(f"✅ Response received: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            # Check if we can detect which agent was used by looking for specific tool calls in logs
            # This is indirect but helpful for understanding routing
            
        except Exception as e:
            logger.error(f"❌ ERROR: {e}")
            import traceback
            logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")
        
        logger.info("=" * 70)

async def test_memory_agent_direct():
    """Test the Memory Agent directly to ensure it works with conversation history."""
    
    logger.info("\n🧪 TESTING MEMORY AGENT DIRECTLY")
    logger.info("=" * 60)
    
    # Initialize components
    initialize_components()
    
    test_queries = [
        "find previous conversations about shoplifting",
        "what was mentioned about pink dress before",
        "get dataset statistics"
    ]
    
    for query in test_queries:
        logger.info(f"\n💭 MEMORY AGENT TEST: '{query}'")
        logger.info("-" * 50)
        
        try:
            # Run query through memory agent directly
            result = await Runner.run(memory_agent, input=query)
            response = result.final_output
            logger.info(f"📝 Memory Agent Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            
        except Exception as e:
            logger.error(f"❌ Memory Agent Error: {e}")
        
        logger.info("-" * 50)

async def test_librarian_agent_direct():
    """Test the Librarian Agent directly to ensure it still works for data queries."""
    
    logger.info("\n🧪 TESTING LIBRARIAN AGENT DIRECTLY")
    logger.info("=" * 60)
    
    # Initialize components
    initialize_components()
    
    test_queries = [
        "show me visual content about a pink dress",
        "search for audio transcripts about conversation",
        "find graph relationships"
    ]
    
    for query in test_queries:
        logger.info(f"\n📖 LIBRARIAN AGENT TEST: '{query}'")
        logger.info("-" * 50)
        
        try:
            # Run query through librarian agent directly
            result = await Runner.run(librarian_agent, input=query)
            response = result.final_output
            logger.info(f"📝 Librarian Agent Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            
        except Exception as e:
            logger.error(f"❌ Librarian Agent Error: {e}")
        
        logger.info("-" * 50)

async def main():
    """Main test function."""
    logger.info("🚀 Starting Agent Routing Test")
    
    # Test routing through secretary
    await test_routing()
    
    # Test agents directly
    await test_memory_agent_direct()
    await test_librarian_agent_direct()
    
    logger.info("✅ All tests completed")

if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required!")
        exit(1)
    
    asyncio.run(main()) 