"""
Main entry point for the multi-agent query service.
"""

import asyncio
import argparse
import logging
import os

from .service import MultiAgentQueryService
from .core import initialize_components, neo4j_driver

async def main():
    """Main function to run the multi-agent query service."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Query Service for Multimodal Data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Database connection arguments
    parser.add_argument(
        "--neo4j-uri", type=str, default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j URI. Can also be set via NEO4J_URI environment variable.",
    )
    parser.add_argument(
        "--neo4j-user", type=str, default=os.environ.get("NEO4J_USER", "neo4j"),
        help="Neo4j username. Can also be set via NEO4J_USER environment variable.",
    )
    parser.add_argument(
        "--neo4j-pass", type=str, dest="neo4j_password", default=os.environ.get("NEO4J_PASSWORD", "password"),
        help="Neo4j password. Can also be set via NEO4J_PASSWORD environment variable.",
    )
    parser.add_argument(
        "--qdrant-host", type=str, default=os.environ.get("QDRANT_HOST", "localhost"),
        help="Qdrant host. Can also be set via QDRANT_HOST environment variable.",
    )
    parser.add_argument(
        "--qdrant-port", type=int, default=int(os.environ.get("QDRANT_PORT", 6333)),
        help="Qdrant port. Can also be set via QDRANT_PORT environment variable.",
    )
    
    # Processing arguments
    parser.add_argument(
        "--embedding-model", type=str, default=os.environ.get("EMBEDDING_MODEL_NAME", "clip-ViT-B-32"),
        help="Embedding model to use for text/image encoding.",
    )
    parser.add_argument(
        "--openai-model", type=str, default=os.environ.get("OPENAI_MODEL", "gpt-4_1-mini-2025-04-14"),
        help="OpenAI model to use for agent conversations.",
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Initializing multi-agent query service...")
        initialize_components()
        logger.info("✅ All components initialized successfully.")
        
        service = MultiAgentQueryService()
        await service.interactive_loop()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.critical(f"❌ Application failed to start: {e}")
    finally:
        if neo4j_driver:
            try:
                neo4j_driver.close()
                logger.info("Neo4j connection closed.")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
        logger.info("Application shutdown complete.")

def run_service():
    """Entry point for running the service."""
    # Ensure OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required!")
        print("Please set it with: export OPENAI_API_KEY=your_api_key_here")
        exit(1)
    
    asyncio.run(main())

if __name__ == "__main__":
    run_service() 