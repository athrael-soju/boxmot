# BoxMOT Query Service

A sophisticated multi-agent query system for intelligent analysis of video tracking data. Built using the OpenAI Agents SDK, this service provides natural language querying capabilities for your BoxMOT video analysis results.

## Overview

The Query Service employs four specialized agents working together to provide comprehensive answers:

- **🏢 Secretary Agent**: Routes queries to the most appropriate specialist
- **🔧 Query Optimizer Agent**: Clarifies and optimizes unclear queries  
- **⚡ Quick Answer Agent**: Handles general questions without data access
- **📚 Librarian Agent**: Performs complex data retrieval and analysis

## Features

- 🤖 **Multi-Agent Architecture**: Specialized agents for different query types
- 🔍 **Vector Search**: Semantic search across entities, frames, and audio
- 📊 **Graph Analysis**: Complex relationship queries using Neo4j
- 🎵 **Audio Integration**: Search and analyze audio transcripts
- 📈 **Temporal Analysis**: Track entity movements over time
- 🛠️ **Custom Queries**: Execute custom Cypher queries for advanced analysis
- 💬 **Interactive Sessions**: Conversational interface for data exploration

## Installation

First, install the OpenAI Agents SDK:

```bash
pip install openai-agents
```

Ensure you have the required dependencies:
```bash
pip install sentence-transformers qdrant-client neo4j minio pillow numpy
```

Set up your environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export NEO4J_PASSWORD="your-neo4j-password"
export HF_TOKEN="your-huggingface-token"  # If using audio features
```

## Quick Start

### Interactive Mode
```bash
python tracking/query_service/cli.py --interactive
```

### Single Query
```bash
python tracking/query_service/cli.py --query "How many people appear in the video?"
```

### Check System Status
```bash
python tracking/query_service/cli.py --status
```

## Query Examples

### 📊 Data Analysis Queries
- "How many people appear in the video?"
- "What entities appear most frequently?"
- "Show me statistics for each entity type"
- "What's the distribution of entities across frames?"

### 🔍 Search Queries
- "Find frames with people walking"
- "Search for entities near cars"
- "Show me all person entities"
- "Find frames with multiple people"

### ⏱️ Temporal Analysis
- "When does entity_5 first appear?"
- "What happens between frames 100 and 200?"
- "Show entity appearances over time"
- "Find entities that appear together"

### 💬 Audio Analysis
- "What was said about the red car?"
- "Find audio segments mentioning 'meeting'"
- "Search transcripts from speaker S1"
- "What audio corresponds to frame 150?"

### ❓ General Questions
- "How does BoxMOT tracking work?"
- "What is ReID in computer vision?"
- "Explain entity relationships"
- "How should I interpret these results?"

## Agent Routing Logic

The **Secretary Agent** automatically routes queries based on content:

| Query Type | Routes To | Example |
|------------|-----------|---------|
| Unclear/Broad | Query Optimizer | "Tell me about stuff" |
| General/Conceptual | Quick Answer | "How does tracking work?" |
| Data-Specific | Librarian | "Find all cars in the video" |

## Data Access Tools

The **Librarian Agent** has access to powerful tools:

### Entity Tools
- `search_entities_by_text()` - Semantic entity search
- `get_entity_details()` - Detailed entity information
- `get_entity_relationships()` - Entity relationship analysis
- `count_entities_by_type()` - Entity statistics

### Frame Tools  
- `search_frames_by_content()` - Frame content search
- `find_entities_in_frame_range()` - Temporal entity analysis

### Audio Tools
- `search_audio_transcripts()` - Transcript search
- Link audio to visual events

### Advanced Tools
- `execute_custom_cypher()` - Custom Neo4j queries
- `get_temporal_analysis()` - Time-based analysis

## Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o                    # Default model

# Database Connections  
QDRANT_HOST=localhost
QDRANT_PORT=6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Model Configuration
EMBEDDING_MODEL_NAME=clip-ViT-B-32
USE_CAPTIONING=False                   # Use captions vs. image storage

# MinIO (if not using captioning)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### CLI Options
```bash
# Model and thresholds
python cli.py --model gpt-4 --similarity-threshold 0.5 --max-iterations 10

# Database connections
python cli.py --neo4j-uri bolt://localhost:7687 --qdrant-host localhost

# Output options
python cli.py --json-output --verbose --no-logs
```

## API Usage

### Programmatic Access
```python
from tracking.query_service import QueryService, QueryServiceConfig

# Initialize service
config = QueryServiceConfig()
service = QueryService(config)

# Synchronous query
result = service.query_sync("How many cars are in the video?")
print(result['response'])

# Asynchronous query
import asyncio
result = await service.query_async("Find people in frames 100-200")

# Interactive session
await service.interactive_session()

# Clean up
service.close()
```

### Context Manager
```python
with QueryService() as service:
    result = service.query_sync("What entities appear most often?")
    print(result['response'])
```

## Advanced Features

### Custom Cypher Queries
The Librarian can execute custom Neo4j queries:
```
"Execute this Cypher query: MATCH (e:Entity)-[:DETECTED_IN]->(f:Frame) WHERE f.frame_idx > 100 RETURN e.class_name, count(f) ORDER BY count(f) DESC"
```

### Temporal Correlation
Link visual and audio events:
```
"What was being said when the person appeared in frame 150?"
```

### Multi-modal Analysis
Combine different data sources:
```
"Show me frames with cars and find any related audio mentions"
```

## System Architecture

```
User Query
    ↓
Secretary Agent (Router)
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│ Query Optimizer │ Quick Answer    │ Librarian Agent │
│ (Clarification) │ (General Info)  │ (Data Analysis) │
└─────────────────┴─────────────────┴─────────────────┘
                                           ↓
                          ┌─────────────────────────────┐
                          │     Data Access Layer       │
                          ├─────────────────────────────┤
                          │ • Vector DB (Qdrant)       │
                          │ • Graph DB (Neo4j)         │
                          │ • Object Storage (MinIO)   │
                          │ • Embedding Models          │
                          └─────────────────────────────┘
```

## Logging and Monitoring

The service automatically logs:
- Query processing times
- Agent routing decisions  
- Data access patterns
- Error conditions

Logs are saved to `runs/query_service/logs/` in JSON format.

## Troubleshooting

### Environment Variable Issues

If your OpenAI API key isn't being read properly:

1. **Check environment variables**
   ```bash
   # Use the built-in debug command
   python tracking/query_service/cli.py --debug-env
   
   # Or run the standalone debug script
   python tracking/query_service/debug_env.py
   ```

2. **Verify .env file location**
   The system looks for `.env` files in these locations (in order):
   - Current working directory: `./env`
   - Project root: `boxmot/.env`
   - Query service directory: `tracking/query_service/.env`

3. **Check .env file format**
   ```bash
   # Your .env file should look like this:
   OPENAI_API_KEY=sk-your-api-key-here
   OPENAI_MODEL=gpt-4.1-mini
   ```

4. **Manual verification**
   ```bash
   # Check if the variable is in your environment
   echo $OPENAI_API_KEY
   
   # Export it manually if needed
   export OPENAI_API_KEY="your-key-here"
   ```

### Common Issues

**Service won't start:**
- Check database connections (Qdrant, Neo4j)
- Verify OpenAI API key
- Ensure required models are accessible

**No query results:**
- Check similarity thresholds
- Verify data exists in databases
- Try broader search terms

**Slow responses:**
- Reduce max_iterations
- Optimize database queries
- Check network connectivity

### Debug Mode
```bash
python cli.py --verbose --query "your query"
```

## Contributing

The query service is designed to be extensible:

1. **Add new tools** in `tools.py`
2. **Extend agents** in `agents.py`  
3. **Add data sources** in `data_access.py`
4. **Customize routing** in the Secretary Agent

## License

This project follows the same license as BoxMOT. 