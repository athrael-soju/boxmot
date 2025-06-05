#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from tracking.agents_infer import MultiAgentQueryService, initialize_components

async def test():
    initialize_components()
    service = MultiAgentQueryService()
    response = await service.process_query('test query')

if __name__ == "__main__":
    asyncio.run(test()) 