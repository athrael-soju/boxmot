#!/usr/bin/env python3
import asyncio
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from tracking.agents_infer import MultiAgentQueryService, initialize_components

# Configure logging to show detailed output
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def quick_test():
    print("🧪 Quick Agent Routing Test")
    print("=" * 40)
    
    initialize_components()
    service = MultiAgentQueryService()
    
    print("\n📝 Testing conversation history query...")
    response = await service.process_query('find previous conversations about shoplifting')
    print(f"✅ Response: {response[:100]}...")
    
    print("\n📝 Testing visual content query...")
    response = await service.process_query('show me a lady in a pink dress')
    print(f"✅ Response: {response[:100]}...")

if __name__ == "__main__":
    asyncio.run(quick_test()) 