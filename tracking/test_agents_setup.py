#!/usr/bin/env python3
"""
Test script to verify multi-agent system setup and dependencies.
Run this before using the main agents_infer.py to ensure everything is configured correctly.
"""

import os
import sys
from pathlib import Path

def test_openai_api_key():
    """Test if OpenAI API key is set."""
    print("🔑 Testing OpenAI API key...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("   Please set it with: export OPENAI_API_KEY=your_api_key_here")
        return False
    elif api_key.startswith("sk-"):
        print("✅ OpenAI API key appears to be set correctly")
        return True
    else:
        print("⚠️  OpenAI API key format looks unusual (should start with 'sk-')")
        return True

def test_python_dependencies():
    """Test if required Python packages are available."""
    print("\n📦 Testing Python dependencies...")
    required_packages = [
        ("agents", "OpenAI Agents SDK"),
        ("openai", "OpenAI Python client"),
        ("sentence_transformers", "SentenceTransformers"),
        ("qdrant_client", "Qdrant client"),
        ("neo4j", "Neo4j driver"),
        ("numpy", "NumPy"),
        ("PIL", "Pillow"),
        ("dotenv", "python-dotenv")
    ]
    
    missing_packages = []
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - not found")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements_agents.txt")
        return False
    return True

def test_qdrant_connection():
    """Test Qdrant database connection."""
    print("\n🔍 Testing Qdrant connection...")
    try:
        from qdrant_client import QdrantClient
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", 6333))
        
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections()
        print(f"✅ Connected to Qdrant at {host}:{port}")
        print(f"   Found {len(collections.collections)} collections")
        
        # Check for expected collections
        collection_names = [c.name for c in collections.collections]
        expected_collections = ["entities", "frames", "audio_transcripts"]
        
        for collection in expected_collections:
            if collection in collection_names:
                info = client.get_collection(collection)
                print(f"   ✅ Collection '{collection}': {info.points_count} points")
            else:
                print(f"   ⚠️  Collection '{collection}': not found (will be created if needed)")
        
        return True
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        print(f"   Make sure Qdrant is running on {host}:{port}")
        return False

def test_neo4j_connection():
    """Test Neo4j database connection."""
    print("\n📊 Testing Neo4j connection...")
    try:
        from neo4j import GraphDatabase, basic_auth
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
        driver.verify_connectivity()
        
        # Test query to get entity count
        with driver.session() as session:
            result = session.run("MATCH (n:Entity) RETURN count(n) as count")
            record = result.single()
            entity_count = record["count"] if record else 0
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = result.single()
            relationship_count = record["count"] if record else 0
        
        print(f"✅ Connected to Neo4j at {uri}")
        print(f"   Entities: {entity_count}, Relationships: {relationship_count}")
        
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print(f"   Make sure Neo4j is running and credentials are correct")
        return False

def test_embedding_model():
    """Test if embedding model can be loaded."""
    print("\n🧠 Testing embedding model...")
    try:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "clip-ViT-B-32")
        
        print(f"   Loading model: {model_name}")
        model = SentenceTransformer(model_name, device='cpu')
        
        # Test encoding
        test_embedding = model.encode(["test text"])
        print(f"✅ Embedding model loaded successfully")
        print(f"   Embedding dimension: {test_embedding.shape[1]}")
        return True
    except Exception as e:
        print(f"❌ Embedding model failed: {e}")
        return False

def test_environment_variables():
    """Test important environment variables."""
    print("\n🌍 Testing environment variables...")
    
    variables = [
        ("OPENAI_API_KEY", "Required for OpenAI API access", True),
        ("NEO4J_URI", "Neo4j connection URI", False),
        ("NEO4J_USER", "Neo4j username", False),
        ("NEO4J_PASSWORD", "Neo4j password", False),
        ("QDRANT_HOST", "Qdrant host", False),
        ("QDRANT_PORT", "Qdrant port", False),
        ("EMBEDDING_MODEL_NAME", "Embedding model name", False),
        ("USE_CAPTIONING", "Image captioning mode", False)
    ]
    
    all_good = True
    for var_name, description, required in variables:
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            display_value = value if var_name != "OPENAI_API_KEY" else f"{value[:8]}..."
            print(f"✅ {var_name}: {display_value}")
        elif required:
            print(f"❌ {var_name}: Not set (required)")
            all_good = False
        else:
            print(f"⚠️  {var_name}: Not set (using default)")
    
    return all_good

def main():
    """Run all tests."""
    print("🚀 Multi-Agent System Setup Test")
    print("=" * 50)
    
    tests = [
        test_python_dependencies,
        test_openai_api_key,
        test_environment_variables,
        test_embedding_model,
        test_qdrant_connection,
        test_neo4j_connection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("🚀 Ready to run the multi-agent system!")
        print("\nNext steps:")
        print("  python tracking/agents_infer.py")
        return 0
    else:
        print(f"❌ Some tests failed ({passed}/{total})")
        print("🔧 Please fix the issues above before running the system.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 