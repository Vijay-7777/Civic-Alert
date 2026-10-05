# LangChain + LangGraph Migration Guide

## Overview

The system has been upgraded to use **LangChain** and **LangGraph** for better:
- ✅ **Reasoning**: LLM decides which tools to use and when
- ✅ **Prompt Management**: Centralized, well-structured prompts
- ✅ **Tool Orchestration**: Automatic tool calling and chaining
- ✅ **State Management**: Better conversation flow and context
- ✅ **Error Handling**: More robust error recovery

## Architecture Comparison

### Old Architecture (Basic Agent)
```
User Message → Intent Detection (Regex) → Direct Function Call → Response
```
- Simple if/else logic
- Manual intent detection
- No reasoning
- Limited context understanding

### New Architecture (LangChain Agent)
```
User Message → LLM Reasoning → Tool Selection → Tool Execution → LLM Synthesis → Response
```
- LLM-based reasoning
- Automatic tool selection
- Multi-step reasoning
- Better context understanding

## Benefits

1. **Better Reasoning**: The LLM understands context and decides which tools to use
2. **Natural Language Understanding**: No need for exact keyword matching
3. **Multi-step Reasoning**: Can chain multiple tools together
4. **Better Prompts**: Structured system prompts guide the LLM
5. **Tool Descriptions**: LLM reads tool descriptions to understand capabilities

## How It Works

### Tool Definitions
Each tool is defined with:
- Clear description of what it does
- Parameter descriptions
- Return value format

The LLM reads these descriptions and decides when to use each tool.

### Example Flow

**User**: "What's the weather like here?"

1. LLM reads the message and location context
2. LLM decides: "User wants weather for their location"
3. LLM calls: `get_weather_tool(lat=29.34, lon=79.51)`
4. Tool returns weather data
5. LLM formats response: "Current weather in Sattal, India: 11°C, Clear..."

## Configuration

### Enable LangChain Agent (Default)
The LangChain agent is enabled by default. To disable it:

```bash
# In .env file
USE_LANGCHAIN_AGENT=false
```

### Model Configuration
Uses the same model as before:
```bash
OLLAMA_MODEL=qwen3:4b  # or qwen2.5:3b, llama3.2:3b, etc.
```

## Tools Available

1. **get_weather_tool**: Get weather for a location
2. **get_local_news_tool**: Get local news for a city
3. **get_india_news_tool**: Get India-wide news
4. **get_local_issues_tool**: Search for local issues using RAG
5. **get_location_info_tool**: Get location info from coordinates
6. **track_report_tool**: Track a report by ID

## Installation

Make sure you have the required packages:

```bash
pip install langchain langchain-ollama langgraph
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

## Testing

Test the new agent:

```python
# The agent automatically uses LangChain if available
# Just restart your backend server
```

## Troubleshooting

### Agent Not Working
1. Check if LangChain is installed: `pip list | grep langchain`
2. Check logs for initialization errors
3. Falls back to basic agent if LangChain fails

### Model Not Found
- Make sure the model is available via Ollama API
- Run: `python backend/check_api_models.py`

### Tool Calling Issues
- Check tool descriptions are clear
- Verify tool parameters match expected types
- Check logs for tool execution errors

## Performance

- **Slightly slower**: LLM reasoning adds ~0.5-1s per request
- **Much smarter**: Better understanding and tool selection
- **More reliable**: Better error handling and fallbacks

## Migration Notes

- Old agent code is preserved in `agent.py`
- Can switch back by setting `USE_LANGCHAIN_AGENT=false`
- Both agents use the same tools and return same format
- Frontend doesn't need any changes

