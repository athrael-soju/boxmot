# Multi-Agent Query Service

A sophisticated multi-agent system for querying multimodal data using OpenAI's Agents SDK.

## Structure

The service is organized into a modular structure for better maintainability and separation of concerns:

```
tracking/query_service/
├── __init__.py              # Package exports
├── README.md               # This documentation
├── core.py                 # Shared utilities and configuration
├── tools.py                # Function tools for agents
├── service.py              # Main service class
├── main.py                 # Entry point and CLI
└── agents/                 # Individual agent definitions
    ├── __init__.py         # Agent exports
    ├── query_optimization.py  # Query optimization specialist
    ├── quick_answer.py     # General questions handler
    ├── memory.py           # Conversation history specialist
    ├── librarian.py        # Multimodal data specialist
    └── secretary.py        # Main coordinator/router
```

## Components

### Core (`core.py`)
- Global client initialization (Qdrant, Neo4j, SentenceTransformer)
- Shared configuration and constants
- Text embedding utilities

### Tools (`tools.py`)
- `@function_tool` decorated functions for agent use
- Vector database query tools
- Graph database query tools
- Conversation history management

### Service (`service.py`)
- `MultiAgentQueryService` class
- Query processing and routing logic
- Interactive loop functionality
- Enhanced logging and tracing

### Agents (`agents/`)

#### Secretary Agent (`secretary.py`)
- **Role**: Main coordinator and router
- **Responsibilities**: 
  - Analyze incoming queries
  - Route to appropriate specialist agents
  - Coordinate multi-agent responses
- **Handoffs**: All other agents

#### Query Optimization Agent (`query_optimization.py`)
- **Role**: Query improvement specialist
- **Responsibilities**:
  - Clarify unclear queries
  - Optimize broad or vague queries
  - Request additional context when needed

#### Quick Answer Agent (`quick_answer.py`)
- **Role**: General questions handler
- **Responsibilities**:
  - Answer general knowledge questions
  - Handle system capability queries
  - Provide quick responses without data access

#### Memory Agent (`memory.py`)
- **Role**: Conversation history specialist
- **Responsibilities**:
  - Retrieve past conversations
  - Maintain conversation continuity
  - Handle all history-related queries
- **Tools**: `retrieve_conversation_history`, `get_dataset_statistics`

#### Librarian Agent (`librarian.py`)
- **Role**: Multimodal data specialist
- **Responsibilities**:
  - Search visual content and video frames
  - Query audio transcripts
  - Explore graph relationships
  - Execute complex data queries
- **Tools**: `retrieve_visual_content`, `retrieve_audio_content`, `get_graph_relationships`, `execute_cypher_query`

## Usage

### Running the Service

1. **Direct execution**:
   ```bash
   cd tracking/query_service
   python main.py
   ```

2. **Module execution**:
   ```bash
   python -m tracking.query_service.main
   ```

3. **Programmatic usage**:
   ```python
   from tracking.query_service import MultiAgentQueryService, initialize_components
   
   initialize_components()
   service = MultiAgentQueryService()
   response = await service.process_query("Your question here")
   ```

### Testing the Structure

Run the test script to verify everything is working:

```bash
python tracking/test_modular_agents.py
```

## Configuration

The service uses environment variables for configuration:

- `OPENAI_API_KEY`: Required for agent functionality
- `NEO4J_URI`: Neo4j connection string (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (default: `password`)
- `QDRANT_HOST`: Qdrant host (default: `localhost`)
- `QDRANT_PORT`: Qdrant port (default: `6333`)
- `EMBEDDING_MODEL_NAME`: SentenceTransformer model (default: `clip-ViT-B-32`)
- `OPENAI_MODEL`: OpenAI model for agents (default: `gpt-4_1-mini-2025-04-14`)
- `USE_CAPTIONING`: Use image captioning vs storage (default: `False`)

## Features

- **Enhanced Logging**: Comprehensive emoji-based logging for query tracing
- **Agent Routing Visualization**: Clear visibility into which agents handle queries
- **Tool Call Tracking**: Monitor which tools are invoked by each agent
- **Conversation Memory**: Automatic storage and retrieval of conversation history
- **Modular Architecture**: Easy to extend and maintain
- **Error Handling**: Robust error handling with detailed tracing

## Migration from agents_infer.py

The original monolithic `agents_infer.py` has been completely refactored into this modular structure. All functionality is preserved while improving:

- **Maintainability**: Each agent in its own file
- **Testability**: Components can be tested independently  
- **Extensibility**: Easy to add new agents or tools
- **Clarity**: Clear separation of concerns
- **Reusability**: Components can be imported and used independently

## Requirements

- OpenAI Agents SDK
- Qdrant client
- Neo4j driver
- SentenceTransformers
- Standard Python async libraries 