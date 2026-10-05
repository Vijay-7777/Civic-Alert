# LangChain + LangGraph Architecture

## Overview

The system has been upgraded to use **LangChain** and **LangGraph** for intelligent agent-based reasoning instead of simple pattern matching.

## Architecture Comparison

### Old Architecture (Basic Agent)
```
User Message 
  → Regex Pattern Matching (if/else)
  → Direct Function Call
  → Response
```
**Problems:**
- No reasoning capability
- Brittle pattern matching
- Can't handle complex queries
- No tool chaining

### New Architecture (LangChain Agent)
```
User Message + Location Context
  → LLM Reasoning (understands intent)
  → Tool Selection (LLM decides which tools)
  → Tool Execution (automatic)
  → LLM Synthesis (formats response)
  → Response
```
**Benefits:**
- ✅ Intelligent reasoning
- ✅ Natural language understanding
- ✅ Automatic tool selection
- ✅ Multi-step reasoning
- ✅ Better error handling

## How It Works

### 1. Tool Definitions
Each tool is defined with clear descriptions:
```python
@tool
def get_weather_tool(location: str = "", lat: float = 0.0, lon: float = 0.0) -> str:
    """
    Get weather information for a location.
    Args:
        location: City name (e.g., "Mumbai", "Delhi")
        lat: Latitude coordinate
        lon: Longitude coordinate
    """
```

The LLM reads these descriptions and understands when to use each tool.

### 2. System Prompt
The system prompt guides the LLM:
- How to handle location queries
- When to use which tools
- How to format responses

### 3. Location Context Injection
When user location is available, it's injected into the message:
```
[USER LOCATION CONTEXT: The user is at Sattal, India (lat=29.34, lon=79.51). 
When they say 'here' or 'my area', use these coordinates.]
```

### 4. Agent Execution Flow
1. User sends message: "whats weather here"
2. LLM reads message + location context
3. LLM reasons: "User wants weather for their location"
4. LLM calls: `get_weather_tool(lat=29.34, lon=79.51)`
5. Tool returns weather data
6. LLM formats response: "Current weather in Sattal, India: 11°C, Clear..."

## Tools Available

1. **get_weather_tool**: Get weather for location/coordinates
2. **get_local_news_tool**: Get local news for city/coordinates
3. **get_india_news_tool**: Get India-wide news
4. **get_local_issues_tool**: Search local issues using RAG
5. **get_location_info_tool**: Get location name from coordinates
6. **track_report_tool**: Track a report by ID

## Configuration

### Enable/Disable
```bash
# In .env file
USE_LANGCHAIN_AGENT=true  # Default: true
```

### Model
Uses the same model configuration:
```bash
OLLAMA_MODEL=qwen3:4b  # or qwen2.5:3b, llama3.2:3b
```

## Key Improvements

### 1. Better Location Handling
- LLM understands "here", "my area", "current location"
- Automatically uses coordinates when provided
- No need for exact keyword matching

### 2. Intelligent Tool Selection
- LLM decides which tools to use
- Can chain multiple tools together
- Handles complex queries naturally

### 3. Better Error Handling
- LLM can reason about errors
- Provides helpful error messages
- Suggests alternatives

### 4. Natural Language Understanding
- No need for exact phrases
- Understands intent, not just keywords
- Handles variations in phrasing

## Example Queries

**Before (Basic Agent):**
- ❌ "whats weather here" → Might not work
- ❌ "really tell my area news" → Might not work
- ❌ "how's the weather?" → Generic response

**After (LangChain Agent):**
- ✅ "whats weather here" → Uses coordinates automatically
- ✅ "really tell my area news" → Understands and uses location
- ✅ "how's the weather?" → Asks for location or uses coordinates
- ✅ "what can you do?" → Lists capabilities intelligently

## Performance

- **Slightly slower**: +0.5-1s per request (LLM reasoning)
- **Much smarter**: Better understanding and responses
- **More reliable**: Better error handling

## Files

- `backend/app/agent_langchain.py` - LangChain agent implementation
- `backend/app/agent.py` - Basic agent (fallback)
- `backend/app/main.py` - Agent initialization with fallback

## Testing

The agent is enabled by default. To test:

1. Restart backend server
2. Check logs for: "✅ Using LangChain agent (better reasoning)"
3. Test with queries like:
   - "whats weather here"
   - "show me local news"
   - "what can you help me with?"

## Troubleshooting

If LangChain agent fails to initialize:
- Falls back to basic agent automatically
- Check logs for error messages
- Verify langchain and langgraph are installed
- Check model is available via Ollama API

