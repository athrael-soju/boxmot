import asyncio
from tracking.query_service.service import QueryService
from tracking.query_service.config import QueryServiceConfig

async def query_video():
    config = QueryServiceConfig()
    service = QueryService(config)
    
    result = await service.query_async("Is there any mention of shoplifting in the video?")
    print(f"Answer: {result['response']}")
    
    service.close()

# Run the query
asyncio.run(query_video())