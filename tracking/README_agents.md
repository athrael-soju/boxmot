# Multi-Agent Query Service

This is a sophisticated multi-agent query service built with OpenAI's Agents SDK that replaces the previous `infer.py` with a more dynamic and effective system for querying multimodal data.

## 🏗️ Architecture

The system consists of 5 specialized agents that work together to handle different types of queries:

### 🎯 Agent Roles

1. **📋 Secretary Agent** (Main Router)
   - Analyzes incoming queries
   - Routes queries to appropriate specialist agents
   - Coordinates responses between multiple agents

2. **🔍 Query Optimization Agent**
   - Clarifies unclear or overly broad queries
   - Optimizes query phrasing for better results
   - Returns clarification requests when needed

3. **⚡ Quick Answer Agent**
   - Handles general questions without data access
   - Answers system capability questions
   - Provides quick responses for common queries

4. **📚 Memory Agent**
   - Retrieves relevant conversation history
   - Maintains context across sessions
   - Uses vector search on past interactions

5. **📖 Librarian Agent** (Most Complex)
   - Searches multimodal data (visual, audio, graph)
   - Executes complex queries across multiple data sources
   - Provides detailed answers with specific data references
   - Can perform multiple retrieval operations for comprehensive answers

## 🚀 Setup

### Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements_agents.txt
   ```

2. **Install OpenAI Agents SDK**
   ```bash
   pip install openai-agents
   ```

3. **Set Environment Variables**
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="your_neo4j_password"
   export QDRANT_HOST="localhost"
   export QDRANT_PORT="6333"
   export EMBEDDING_MODEL_NAME="clip-ViT-B-32"
   ```

4. **Ensure Services are Running**
   - Qdrant vector database (port 6333)
   - Neo4j graph database (port 7687)
   - MinIO object storage (if using image storage mode)

## 🎮 Usage

### Interactive Mode

Run the service in interactive mode:

```bash
python tracking/agents_infer.py
```

### Command Line Options

```bash
python tracking/agents_infer.py \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-user neo4j \
  --neo4j-pass password \
  --qdrant-host localhost \
  --qdrant-port 6333 \
  --embedding-model clip-ViT-B-32 \
  --openai-model gpt-4 \
  --log-level INFO
```

## 🔄 Query Flow

1. **User submits query** → Secretary Agent
2. **Secretary analyzes and routes** to appropriate agent:
   - Unclear query → Query Optimization Agent
   - General question → Quick Answer Agent  
   - Reference to past conversation → Memory Agent
   - Data query → Librarian Agent
3. **Specialist agent processes** the query using available tools
4. **Response** is returned to user
5. **Conversation is stored** for future reference

## 🛠️ Available Tools

### Librarian Agent Tools

- `retrieve_visual_content()` - Search visual data (entities, frames)
- `retrieve_audio_content()` - Search audio transcripts
- `get_graph_relationships()` - Query entity relationships
- `execute_cypher_query()` - Run custom Cypher queries
- `get_dataset_statistics()` - Get data collection stats

### Memory Agent Tools

- `retrieve_conversation_history()` - Search past conversations

## 💬 Example Queries

### General Questions (Quick Answer Agent)
- "What can this system do?"
- "How many agents are available?"
- "What is computer vision?"

### Data Queries (Librarian Agent)
- "Show me all detected people in the video"
- "What was said between 2:30 and 3:00 in the audio?"
- "Find relationships between entity_123 and other objects"
- "How many entities are stored in the database?"

### Memory Queries (Memory Agent)
- "What did we discuss about cars earlier?"
- "Remind me about the previous analysis"

### Unclear Queries (Query Optimization Agent)
- "Tell me about the data" → Gets optimized to more specific query
- "Show me stuff" → Requests clarification

## 📊 Data Sources

The Librarian Agent can access:

1. **Visual Content**
   - Entity detections with bounding boxes
   - Video frames with timestamps
   - Image captions (if captioning mode enabled)
   - MinIO stored images (if storage mode enabled)

2. **Audio Content**
   - Speaker-diarized transcripts
   - Temporal segments with timestamps
   - Speaker labels and confidence scores

3. **Graph Data**
   - Entity relationships and interactions
   - Temporal connections between entities
   - Custom Cypher query results

4. **Conversation History**
   - Previous user queries and AI responses
   - Timestamped interaction logs
   - Context for maintaining conversation continuity

## 🔧 Configuration

### Environment Variables

- `USE_CAPTIONING` - Use image captioning instead of MinIO storage
- `OPENAI_MODEL` - OpenAI model for agent conversations (default: gpt-4)
- `EMBEDDING_MODEL_NAME` - Embedding model for vector search
- `QDRANT_*` - Qdrant connection settings
- `NEO4J_*` - Neo4j connection settings
- `MINIO_*` - MinIO settings (if not using captioning)

### Collection Names

- `entities` - Visual entity detections
- `frames` - Video frame embeddings
- `audio_transcripts` - Audio transcript embeddings
- `conversation_history` - Previous conversations (auto-created)

## 📝 Logging

The system provides comprehensive logging with:
- Query processing traces
- Agent routing decisions
- Tool execution results
- Error handling and debugging info
- Timestamped interaction logs saved to disk

Log files are saved to: `runs/track/exp/agents_infer/{timestamp}/`

## 🔄 Conversation Memory

The system automatically:
- Stores every user query and AI response
- Creates vector embeddings for conversation turns
- Enables retrieval of relevant past interactions
- Maintains conversation continuity across sessions

## 🚨 Error Handling

The system includes robust error handling for:
- Database connection failures
- Missing data collections
- Embedding model errors
- OpenAI API failures
- Tool execution errors

## 🎯 Extension Points

To add new capabilities:

1. **New Tools**: Add `@function_tool` decorated functions
2. **New Agents**: Create new Agent instances with specific roles
3. **New Data Sources**: Extend librarian tools for additional databases
4. **Custom Routing**: Modify secretary agent instructions for new routing logic

## 🔍 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   - Set the environment variable with your OpenAI API key

2. **"No graph database connection"**
   - Ensure Neo4j is running and credentials are correct

3. **"Collection not found"**
   - Run the main tracking pipeline first to populate data collections

4. **"Embedding model failed to load"**
   - Check internet connection for model download
   - Verify model name in EMBEDDING_MODEL_NAME

### Debug Mode

Run with debug logging:
```bash
python tracking/agents_infer.py --log-level DEBUG
```

This enhanced multi-agent system provides a much more sophisticated and capable interface for querying your multimodal data compared to the previous single-agent approach. 