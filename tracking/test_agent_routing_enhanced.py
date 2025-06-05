#!/usr/bin/env python3
"""
Test script to verify enhanced agent routing and logging.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to Python path so we can import the agents module
sys.path.append(str(Path(__file__).parent.parent))

from tracking.agents_infer import MultiAgentQueryService, initialize_components

# Setup logging to see all output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def test_agent_routing():
    """Test different types of queries to see which agents handle them."""
    
    print("🧪 Testing Enhanced Agent Routing & Logging")
    print("=" * 60)
    
    # Initialize the system
    try:
        print("🚀 Initializing components...")
        initialize_components()
        print("✅ Components initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return
    
    service = MultiAgentQueryService()
    
    # Test cases that should route to different agents
    test_queries = [
        {
            "query": "find previous conversations about shoplifting",
            "expected_agent": "Memory Agent",
            "description": "Conversation history query"
        },
        {
            "query": "what did I see yesterday?", 
            "expected_agent": "Memory Agent",
            "description": "Memory recall query"
        },
        {
            "query": "show me visual content with a lady in a pink dress",
            "expected_agent": "Librarian Agent", 
            "description": "Visual content retrieval"
        },
        {
            "query": "what is the weather like?",
            "expected_agent": "Quick Answer Agent",
            "description": "General knowledge question"
        },
        {
            "query": "tell me something random and unclear",
            "expected_agent": "Query Optimization Agent",
            "description": "Unclear query needing clarification"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🧪 Test Case {i}: {test_case['description']}")
        print(f"📝 Query: '{test_case['query']}'")
        print(f"🎯 Expected Agent: {test_case['expected_agent']}")
        print("-" * 50)
        
        try:
            response = await service.process_query(test_case['query'])
            print(f"✅ Response received: {response[:100]}{'...' if len(response) > 100 else ''}")
        except Exception as e:
            print(f"❌ Error in test case {i}: {e}")
        
        print("-" * 50)
        
        # Small delay between tests for clarity
        await asyncio.sleep(1)
    
    print("\n🏁 All test cases completed!")
    print("Check the logs above to see which agents were invoked for each query.")

if __name__ == "__main__":
    try:
        asyncio.run(test_agent_routing())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 