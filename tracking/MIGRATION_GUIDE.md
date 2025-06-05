# Migration Guide: From `infer.py` to Multi-Agent System

This guide helps you transition from the previous single-agent `infer.py` to the new sophisticated multi-agent query service.

## 🆚 Key Differences

### Old System (`infer.py`)
- Single monolithic query handler
- Direct function calls for data retrieval
- Basic prompt building and OpenAI API calls
- Simple interactive loop
- Limited query understanding

### New System (`agents_infer.py`)
- **5 specialized agents** with different roles
- **Intelligent query routing** based on intent
- **Conversation memory** across sessions
- **Advanced error handling** and logging
- **Extensible architecture** for new capabilities

## 🔄 Functional Mapping

### What Changed

| Old Function | New Equivalent | Notes |
|-------------|----------------|--------|
| `interactive_loop()` | `MultiAgentQueryService.interactive_loop()` | Enhanced with agent routing |
| `retrieve_similar_content()` | `retrieve_visual_content()` + `retrieve_audio_content()` | Split into specialized functions |
| `retrieve_graph_context()` | `get_graph_relationships()` + `execute_cypher_query()` | More powerful graph querying |
| `build_prompt()` | Agent instructions + tool results | Dynamic prompt building per agent |
| Direct OpenAI calls | OpenAI Agents SDK | Sophisticated agent orchestration |

### What's New

1. **Query Classification**: Automatic routing to appropriate specialists
2. **Conversation Memory**: Persistent storage and retrieval of past interactions
3. **Query Optimization**: Automatic clarification of unclear queries
4. **Quick Answers**: Fast responses for general questions
5. **Advanced Logging**: Comprehensive trace logging with timestamps
6. **Error Recovery**: Robust error handling across all components

## 🚀 Migration Steps

### 1. Install New Dependencies

```bash
# Install OpenAI Agents SDK
pip install openai-agents

# Install additional requirements
pip install -r requirements_agents.txt
```

### 2. Update Environment Variables

The new system uses the same core environment variables but adds some new ones:

```bash
# Existing (keep these)
export OPENAI_API_KEY="your_key"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"

# New (optional, with sensible defaults)
export OPENAI_MODEL="gpt-4"  # or gpt-3.5-turbo for cost savings
export EMBEDDING_MODEL_NAME="clip-ViT-B-32"
```

### 3. Test Your Setup

Before migrating, verify everything works:

```bash
python tracking/test_agents_setup.py
```

### 4. Update Your Scripts

If you were importing functions from `infer.py`:

#### Old Code:
```python
from tracking.infer import retrieve_similar_content, retrieve_graph_context

# Direct function calls
content = retrieve_similar_content(query, embedding, qdrant_client, logger)
graph_data = retrieve_graph_context(entity_ids)
```

#### New Code:
```python
from tracking.agents_infer import MultiAgentQueryService

# Agent-based querying
service = MultiAgentQueryService()
response = await service.process_query("Find all people in the video")
```

### 5. Migrate Custom Functions

If you added custom functions to `infer.py`:

#### Add New Tools:
```python
@function_tool
def your_custom_function(param1: str, param2: int) -> str:
    """Your custom functionality."""
    # Your implementation
    return result

# Add to appropriate agent
enhanced_librarian = Agent(
    name="Enhanced Librarian",
    instructions="...",
    tools=[retrieve_visual_content, your_custom_function]
)
```

#### Add New Agents:
```python
your_specialist_agent = Agent(
    name="Your Specialist",
    instructions="Handle specific domain queries...",
    tools=[your_custom_tools]
)

# Update secretary routing
secretary_agent = Agent(
    name="Secretary Agent",
    instructions="Route to specialists including Your Specialist for domain-specific queries...",
    handoffs=[..., your_specialist_agent]
)
```

## 🎯 Usage Patterns

### Interactive Usage

#### Old Way:
```bash
python tracking/infer.py
# Basic Q&A loop
```

#### New Way:
```bash
python tracking/agents_infer.py
# Rich multi-agent interaction with routing and memory
```

### Programmatic Usage

#### Old Way:
```python
# Direct function calls
result = process_query_manually(query, all_components)
```

#### New Way:
```python
# Agent orchestration
service = MultiAgentQueryService()
result = await service.process_query(query)
```

## 📊 Performance Considerations

### Response Times
- **Quick Answer Agent**: Faster for general queries (no data access)
- **Librarian Agent**: Similar to old system for data queries
- **Secretary Agent**: Small overhead for routing decisions
- **Memory Agent**: Additional time for conversation history search

### Resource Usage
- **Memory**: Slightly higher due to agent framework
- **Network**: Additional OpenAI API calls for agent decisions
- **Storage**: Conversation history stored in new Qdrant collection

### Cost Optimization
- Use `gpt-3.5-turbo` instead of `gpt-4` for cost savings
- Quick Answer Agent reduces API calls for simple queries
- Conversation memory enables context-aware responses

## 🔧 Configuration Options

### Agent Behavior Tuning

Customize agent instructions for your use case:

```python
# Example: More technical librarian
technical_librarian = Agent(
    name="Technical Librarian",
    instructions="""You are a technical data analyst specializing in computer vision and audio processing.
    Provide detailed technical explanations with specific metrics, confidence scores, and timestamps.
    Use technical terminology and include data quality assessments.""",
    tools=[retrieve_visual_content, retrieve_audio_content, get_dataset_statistics]
)
```

### Conversation Memory Settings

```python
# Adjust conversation history retrieval
TARGET_CONVERSATION_TOP_K = 10  # Retrieve more history
MIN_CONVERSATION_SIMILARITY_THRESHOLD = 0.20  # Lower threshold for broader context
```

## 🐛 Troubleshooting Migration Issues

### Common Problems

1. **"agents module not found"**
   ```bash
   pip install openai-agents
   ```

2. **"Conversation collection not found"**
   - Normal on first run - collection is auto-created

3. **"Agent routing not working as expected"**
   - Check OpenAI API key and model availability
   - Review agent instructions for clarity

4. **"Slower response times"**
   - Consider using `gpt-3.5-turbo` for faster responses
   - Check network connectivity to OpenAI

### Debugging

Enable debug logging to trace agent decisions:

```bash
python tracking/agents_infer.py --log-level DEBUG
```

### Performance Monitoring

Compare old vs new performance:

```python
# Add timing to your queries
import time
start_time = time.time()
result = await service.process_query(query)
print(f"Query took {time.time() - start_time:.2f} seconds")
```

## 🎉 Benefits After Migration

### Immediate Benefits
- **Better Query Understanding**: Automatic classification and routing
- **Conversation Context**: Remembers previous interactions
- **Error Recovery**: Graceful handling of failures
- **Rich Logging**: Detailed traces for debugging

### Long-term Benefits
- **Extensibility**: Easy to add new agents and capabilities
- **Scalability**: Agent-based architecture supports complex workflows
- **Maintainability**: Modular design with clear separation of concerns
- **User Experience**: More natural and intelligent interactions

## 🔮 Future Enhancements

The new architecture enables:

- **Multi-step Reasoning**: Agents can collaborate on complex queries
- **Custom Workflows**: Chain agents for specific use cases
- **Real-time Updates**: Integrate with streaming data sources
- **User Personalization**: Learn from individual usage patterns
- **External Integrations**: Connect to additional data sources and APIs

## 📞 Support

If you encounter issues during migration:

1. **Check the setup**: Run `python tracking/test_agents_setup.py`
2. **Review logs**: Enable debug logging for detailed traces
3. **Consult README**: See `tracking/README_agents.md` for detailed documentation
4. **Compare functionality**: Verify all your use cases are covered

The new multi-agent system provides a much more sophisticated and capable foundation for querying your multimodal data! 