#!/usr/bin/env python3
"""
Command Line Interface for BoxMOT Query Service

Provides both interactive and single-query modes for the query service.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from tracking.query_service.service import QueryService
from tracking.query_service.config import QueryServiceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BoxMOT Query Service CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cli.py --interactive
  
  # Single query
  python cli.py --query "How many people are in the video?"
  
  # Check system status
  python cli.py --status
  
  # Query with custom config
  python cli.py --query "Find cars" --model gpt-4.1-mini --similarity-threshold 0.5
        """
    )
    
    # Query options
    query_group = parser.add_mutually_exclusive_group()
    query_group.add_argument(
        '--query', '-q',
        type=str,
        help='Single query to process'
    )
    query_group.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive query session'
    )
    query_group.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show system status and exit'
    )
    query_group.add_argument(
        '--debug-env',
        action='store_true',
        help='Show environment variables debug info and exit'
    )
    
    # Configuration options
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='OpenAI model to use (default: from env or gpt-4o)'
    )
    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=None,
        help='Similarity threshold for vector searches (default: 0.3)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=None,
        help='Maximum agent iterations per query (default: 5)'
    )
    
    # Database connection options
    parser.add_argument(
        '--qdrant-host',
        type=str,
        default=None,
        help='Qdrant host (default: localhost)'
    )
    parser.add_argument(
        '--qdrant-port',
        type=int,
        default=None,
        help='Qdrant port (default: 6333)'
    )
    parser.add_argument(
        '--neo4j-uri',
        type=str,
        default=None,
        help='Neo4j URI (default: bolt://localhost:7687)'
    )
    parser.add_argument(
        '--neo4j-user',
        type=str,
        default=None,
        help='Neo4j username (default: neo4j)'
    )
    parser.add_argument(
        '--neo4j-password',
        type=str,
        default=None,
        help='Neo4j password (default: password)'
    )
    
    # Output options
    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--no-logs',
        action='store_true',
        help='Disable saving query logs'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()

def create_config_from_args(args) -> QueryServiceConfig:
    """Create configuration object from command line arguments"""
    config = QueryServiceConfig()
    
    # Update config with provided arguments
    if args.model:
        config.openai_model = args.model
    if args.similarity_threshold is not None:
        config.similarity_threshold = args.similarity_threshold
    if args.max_iterations is not None:
        config.max_query_iterations = args.max_iterations
    if args.qdrant_host:
        config.qdrant_host = args.qdrant_host
    if args.qdrant_port:
        config.qdrant_port = args.qdrant_port
    if args.neo4j_uri:
        config.neo4j_uri = args.neo4j_uri
    if args.neo4j_user:
        config.neo4j_user = args.neo4j_user
    if args.neo4j_password:
        config.neo4j_password = args.neo4j_password
    
    return config

async def handle_single_query(service: QueryService, query: str, args) -> None:
    """Handle a single query"""
    try:
        result = await service.query_async(query, save_logs=not args.no_logs)
        
        if args.json_output:
            print(json.dumps(result, indent=2))
        else:
            if result["status"] == "success":
                print(f"\nQuery: {result['user_input']}")
                print(f"Response: {result['response']}")
                print(f"Processing time: {result['processing_time_seconds']:.3f}s")
                if args.verbose:
                    print(f"Agent used: {result.get('agent_used', 'Unknown')}")
                    print(f"Query ID: {result['query_id']}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                if args.verbose:
                    print(f"Query ID: {result['query_id']}")
                    print(f"Processing time: {result['processing_time_seconds']:.3f}s")
    except Exception as e:
        if args.json_output:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"Error processing query: {e}")

def handle_status(service: QueryService, args) -> None:
    """Handle status request"""
    try:
        status = service.get_system_status()
        
        if args.json_output:
            print(json.dumps(status, indent=2))
        else:
            print("\n" + "="*50)
            print("      BoxMOT Query Service Status")
            print("="*50)
            print(f"Service Status: {status.get('service_status', 'Unknown')}")
            print(f"Data Access: {status.get('data_access_status', 'Unknown')}")
            print(f"Available Agents: {', '.join(status.get('agents_available', []))}")
            
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
                    print("  Entity Counts:")
                    for entity_type, count in list(entity_counts.items())[:5]:  # Show top 5
                        print(f"    {entity_type}: {count}")
                    if len(entity_counts) > 5:
                        print(f"    ... and {len(entity_counts) - 5} more types")
            
            if status.get('data_access_error'):
                print(f"\nData Access Error: {status['data_access_error']}")
            
            print("="*50)
    except Exception as e:
        if args.json_output:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"Error getting status: {e}")

async def main():
    """Main CLI function"""
    args = parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Handle debug environment variables option
    if args.debug_env:
        config.debug_env_vars()
        return
    
    try:
        # Initialize query service
        logger.info("Initializing BoxMOT Query Service...")
        with QueryService(config) as service:
            
            if args.status:
                handle_status(service, args)
            
            elif args.query:
                await handle_single_query(service, args.query, args)
            
            elif args.interactive:
                await service.interactive_session()
            
            else:
                # Default to interactive mode if no specific action
                print("No action specified. Starting interactive mode...")
                await service.interactive_session()
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 