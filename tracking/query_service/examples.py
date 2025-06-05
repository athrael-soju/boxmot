#!/usr/bin/env python3
"""
Example Usage of BoxMOT Query Service

This script demonstrates various ways to use the query service.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from tracking.query_service.service import QueryService
from tracking.query_service.config import QueryServiceConfig

async def basic_usage_example():
    """Basic usage of the query service"""
    print("="*60)
    print("Basic Usage Example")
    print("="*60)
    
    # Create a basic configuration
    config = QueryServiceConfig()
    
    try:
        # Initialize the service
        with QueryService(config) as service:
            
            # Example queries
            queries = [
                "How many people appear in the video?",
                "What is ReID in computer vision?", 
                "Find all car entities",
                "Show me entity statistics"
            ]
            
            for query in queries:
                print(f"\nQuery: {query}")
                print("-" * 40)
                
                result = service.query_sync(query, save_logs=False)
                
                if result["status"] == "success":
                    print(f"Response: {result['response']}")
                    print(f"Agent: {result.get('agent_used', 'Unknown')}")
                    print(f"Time: {result['processing_time_seconds']:.3f}s")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                
                print()
    
    except Exception as e:
        print(f"Error in basic usage example: {e}")

async def advanced_query_example():
    """Advanced querying with custom configuration"""
    print("="*60)
    print("Advanced Query Example")
    print("="*60)
    
    # Custom configuration
    config = QueryServiceConfig()
    config.similarity_threshold = 0.4  # Lower threshold for more results
    config.max_query_iterations = 8    # More iterations for complex queries
    
    try:
        with QueryService(config) as service:
            
            # Complex queries that might require multiple agent interactions
            complex_queries = [
                "I want to know about entities that appear together frequently. Can you analyze their relationships and tell me which ones have the strongest connections?",
                "Find frames between 100 and 200 and tell me what entities appear in them, then search for any audio that mentions those entity types",
                "What happens in the video over time? Show me a temporal analysis of entity appearances."
            ]
            
            for query in complex_queries:
                print(f"\nComplex Query: {query}")
                print("-" * 80)
                
                result = await service.query_async(query, save_logs=False)
                
                if result["status"] == "success":
                    print(f"Response: {result['response']}")
                    print(f"Processing time: {result['processing_time_seconds']:.3f}s")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                
                print()
    
    except Exception as e:
        print(f"Error in advanced query example: {e}")

async def agent_routing_demo():
    """Demonstrate how different queries are routed to different agents"""
    print("="*60)
    print("Agent Routing Demonstration")
    print("="*60)
    
    config = QueryServiceConfig()
    
    try:
        with QueryService(config) as service:
            
            # Queries designed to hit different agents
            routing_examples = [
                ("General Question", "How does object tracking work in computer vision?"),
                ("Data Query", "Count all the person entities in the database"),
                ("Unclear Query", "Tell me about stuff in the video"),
                ("Temporal Query", "When do cars first appear?"),
                ("Audio Query", "Search for audio mentioning 'person'"),
            ]
            
            for query_type, query in routing_examples:
                print(f"\n{query_type}: {query}")
                print("-" * 60)
                
                result = service.query_sync(query, save_logs=False)
                
                if result["status"] == "success":
                    print(f"Routed to: {result.get('agent_used', 'Unknown')} Agent")
                    print(f"Response: {result['response'][:200]}...")  # Truncate long responses
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                
                print()
    
    except Exception as e:
        print(f"Error in agent routing demo: {e}")

async def system_status_example():
    """Demonstrate system status checking"""
    print("="*60)
    print("System Status Example")
    print("="*60)
    
    config = QueryServiceConfig()
    
    try:
        with QueryService(config) as service:
            status = service.get_system_status()
            
            print("System Status:")
            print(f"  Service: {status.get('service_status', 'Unknown')}")
            print(f"  Data Access: {status.get('data_access_status', 'Unknown')}")
            print(f"  Available Agents: {', '.join(status.get('agents_available', []))}")
            
            config_info = status.get('config', {})
            print(f"\nConfiguration:")
            print(f"  Model: {config_info.get('model', 'Unknown')}")
            print(f"  Max Iterations: {config_info.get('max_iterations', 'Unknown')}")
            print(f"  Similarity Threshold: {config_info.get('similarity_threshold', 'Unknown')}")
            
            data_stats = status.get('data_statistics', {})
            if data_stats:
                print(f"\nData Statistics:")
                print(f"  Entity Types: {data_stats.get('total_entity_types', 0)}")
                entity_counts = data_stats.get('entity_counts', {})
                if entity_counts:
                    print("  Top Entity Types:")
                    for entity_type, count in list(entity_counts.items())[:3]:
                        print(f"    {entity_type}: {count}")
            
            if status.get('data_access_error'):
                print(f"\nData Access Warning: {status['data_access_error']}")
    
    except Exception as e:
        print(f"Error in system status example: {e}")

async def error_handling_example():
    """Demonstrate error handling"""
    print("="*60)
    print("Error Handling Example")
    print("="*60)
    
    config = QueryServiceConfig()
    
    try:
        with QueryService(config) as service:
            
            # Examples of queries that might cause different types of errors
            error_queries = [
                "Execute this invalid Cypher: INVALID SYNTAX",
                "",  # Empty query
                "Search for nonexistent_entity_12345",
            ]
            
            for query in error_queries:
                print(f"\nTesting query: '{query}'")
                print("-" * 40)
                
                result = service.query_sync(query, save_logs=False)
                
                print(f"Status: {result['status']}")
                if result['status'] == 'error':
                    print(f"Error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"Response: {result.get('response', 'No response')}")
                
                print()
    
    except Exception as e:
        print(f"Error in error handling example: {e}")

async def main():
    """Run all examples"""
    print("BoxMOT Query Service Examples")
    print("=" * 80)
    
    examples = [
        ("Basic Usage", basic_usage_example),
        ("Advanced Queries", advanced_query_example),
        ("Agent Routing", agent_routing_demo),
        ("System Status", system_status_example),
        ("Error Handling", error_handling_example),
    ]
    
    for name, example_func in examples:
        try:
            print(f"\n\n🎯 Running {name} Example...")
            await example_func()
            print(f"✅ {name} example completed")
        except Exception as e:
            print(f"❌ Error in {name} example: {e}")
        
        # Pause between examples
        await asyncio.sleep(1)
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("\nTo run the interactive service:")
    print("python tracking/query_service/cli.py --interactive")

if __name__ == "__main__":
    asyncio.run(main()) 