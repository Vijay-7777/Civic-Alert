"""
LangChain + LangGraph based agent for Civic Alert
Provides better reasoning, prompt management, and tool orchestration
"""

from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

# Try to import Gemini support
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: langchain-google-genai not installed. Gemini API not available.")

# Prefer LangGraph ReAct agent to avoid tool-calling requirements
try:
    from langgraph.prebuilt import create_react_agent as create_agent
    USE_CREATE_AGENT = True
    AGENT_PARAM_NAME = "prompt"
except ImportError:
    try:
        from langchain.agents import create_agent
        USE_CREATE_AGENT = True
        AGENT_PARAM_NAME = "system_prompt"
    except ImportError:
        USE_CREATE_AGENT = False
        AGENT_PARAM_NAME = None
        print("Warning: LangChain agent creation not available, will use basic agent")
from .config import OLLAMA_URL, OLLAMA_MODEL, GEMINI_API_KEY, GEMINI_MODEL, USE_GEMINI_API
from .tools import (
    get_india_news,
    get_local_news,
    get_weather,
    reverse_geocode,
    geocode_location,
    rag_local_issues,
    track_report
)

# Initialize LLM based on configuration
def get_llm():
    """Get the LLM instance - either Gemini or Ollama"""
    if USE_GEMINI_API and GEMINI_API_KEY and GEMINI_AVAILABLE:
        try:
            return ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GEMINI_API_KEY,
                temperature=0.7,
                max_output_tokens=1024,
            )
        except Exception as e:
            print(f"Failed to initialize Gemini, falling back to Ollama: {e}")
            # Fall back to Ollama
    
    # Default to Ollama
    model_name = OLLAMA_MODEL
    return ChatOllama(
        model=model_name,
        base_url=OLLAMA_URL.replace("/api/generate", ""),
        temperature=0.7,
        num_predict=1024,
    )

# Define tools as LangChain tools
@tool
def get_weather_tool(location: str = "", lat: float = 0.0, lon: float = 0.0) -> str:
    """
    Get weather information for a location.
    
    Args:
        location: City name (e.g., "Mumbai", "Delhi"). If not provided, uses lat/lon.
        lat: Latitude coordinate
        lon: Longitude coordinate
    
    Returns:
        Weather information as a formatted string
    """
    try:
        # Handle location parameter
        if location and location.strip():
            # Geocode the location
            geo_result = geocode_location(location)
            if geo_result.get("success"):
                lat = geo_result["data"]["lat"]
                lon = geo_result["data"]["lon"]
            else:
                return f"Could not find location: {location}"
        
        # Use coordinates if provided and valid
        if lat and lon and (lat != 0.0 or lon != 0.0):
            result = get_weather(lat, lon)
            if result.get("success"):
                weather = result["data"]
                return f"Weather in {weather['city']}, {weather['country']}: {weather['temperature']}°C, {weather['description']}, Humidity: {weather['humidity']}%"
            else:
                return result.get("message", "Failed to get weather")
        else:
            return "Please provide a location name or coordinates"
    except Exception as e:
        return f"Error getting weather: {str(e)}"

@tool
def get_local_news_tool(city: str = "", lat: float = 0.0, lon: float = 0.0) -> str:
    """
    Get local news for a city or location.
    
    Args:
        city: City name (e.g., "Mumbai", "Delhi"). If not provided, uses lat/lon to determine city.
        lat: Latitude coordinate
        lon: Longitude coordinate
    
    Returns:
        News articles as a formatted string
    """
    try:
        # Use coordinates if city not provided
        if (not city or not city.strip()) and lat and lon and (lat != 0.0 or lon != 0.0):
            # Reverse geocode to get city
            location_result = reverse_geocode(lat, lon)
            if location_result.get("success"):
                city = location_result["data"]["city"]
                state = location_result["data"].get("state", "")
                if state:
                    city = f"{city}, {state}"
        
        if city and city.strip():
            result = get_local_news(city, lat, lon, try_neighbors=True)
            if result.get("success"):
                articles = result["data"]
                if articles:
                    news_text = f"Found {len(articles)} news articles for {city}:\n\n"
                    for i, article in enumerate(articles[:5], 1):
                        news_text += f"{i}. {article.get('title', 'No title')}\n"
                        if article.get('description'):
                            news_text += f"   {article.get('description', '')[:100]}...\n"
                        news_text += f"   Source: {article.get('source', 'Unknown')}\n\n"
                    return news_text
                else:
                    return f"No news articles found for {city}"
            else:
                return result.get("message", "Failed to get local news")
        else:
            return "Please provide a city name or coordinates"
    except Exception as e:
        return f"Error getting local news: {str(e)}"

@tool
def get_india_news_tool() -> str:
    """
    Get latest news from India.
    
    Returns:
        India news articles as a formatted string
    """
    try:
        result = get_india_news()
        if result.get("success"):
            articles = result["data"]
            if articles:
                news_text = "Latest India News:\n\n"
                for i, article in enumerate(articles[:5], 1):
                    news_text += f"{i}. {article.get('title', 'No title')}\n"
                    if article.get('description'):
                        news_text += f"   {article.get('description', '')[:100]}...\n"
                    news_text += f"   Source: {article.get('source', 'Unknown')}\n\n"
                return news_text
            else:
                return "No news articles found"
        else:
            return result.get("message", "Failed to get India news")
    except Exception as e:
        return f"Error getting India news: {str(e)}"

@tool
def get_local_issues_tool(query: str, lat: float = 0.0, lon: float = 0.0) -> str:
    """
    Search for local issues/problems in the area using RAG.
    
    Args:
        query: Search query (e.g., "potholes", "garbage", "water issues")
        lat: Latitude coordinate
        lon: Longitude coordinate
    
    Returns:
        Local issues as a formatted string
    """
    try:
        # Only use coordinates if they're valid (not default 0.0)
        use_coords = lat and lon and (lat != 0.0 or lon != 0.0)
        result = rag_local_issues(query, lat if use_coords else None, lon if use_coords else None)
        if result.get("success"):
            issues = result["data"]
            if issues:
                issues_text = f"Found {len(issues)} local issues:\n\n"
                for i, issue in enumerate(issues[:5], 1):
                    issues_text += f"{i}. {issue.get('title', issue.get('description', 'Issue'))}\n"
                    if issue.get('location'):
                        issues_text += f"   Location: {issue.get('location')}\n"
                    issues_text += "\n"
                return issues_text
            else:
                return "No local issues found matching your query"
        else:
            return result.get("message", "Failed to search local issues")
    except Exception as e:
        return f"Error searching local issues: {str(e)}"

@tool
def get_location_info_tool(lat: float, lon: float) -> str:
    """
    Get location information from coordinates (reverse geocoding).
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
    
    Returns:
        Location information as a formatted string
    """
    try:
        result = reverse_geocode(lat, lon)
        if result.get("success"):
            data = result["data"]
            city = data.get("city", "")
            state = data.get("state", "")
            country = data.get("country", "")
            location_str = f"{city}"
            if state:
                location_str += f", {state}"
            if country:
                location_str += f", {country}"
            return f"Your location: {location_str}"
        else:
            return result.get("message", "Failed to get location information")
    except Exception as e:
        return f"Error getting location: {str(e)}"

@tool
def track_report_tool(report_id: int) -> str:
    """
    Track a report by its ID.
    
    Args:
        report_id: The report ID to track
    
    Returns:
        Report status and details as a formatted string
    """
    try:
        result = track_report(report_id)
        if result.get("success"):
            report = result["data"]
            status = report.get("status", "Unknown")
            title = report.get("title", "No title")
            return f"Report #{report_id}: {title}\nStatus: {status}"
        else:
            return result.get("message", f"Report {report_id} not found")
    except Exception as e:
        return f"Error tracking report: {str(e)}"

# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful Civic Alert assistant for a crime reporting and community issues platform. You help users with:
- Crime reporting and tracking
- Local news and weather information  
- Community issues and concerns
- General safety and security advice

CRITICAL LOCATION HANDLING RULES:
1. When users ask about "here", "my area", "my location", "current location", or "in my area", you MUST use the coordinates (lat/lon) provided in the context
2. If coordinates are provided in the context, ALWAYS pass them to tools (lat and lon parameters)
3. For weather queries with "here" or "my area", use the coordinates, NOT a location name
4. For local news with "here" or "my area", use the coordinates to get the city name
5. Only use location names when the user explicitly mentions a specific city/place

TOOL USAGE GUIDELINES:
- Use get_weather_tool with lat/lon when user says "here" or "my area"
- Use get_local_news_tool with lat/lon when user asks for news "here" or "in my area"
- Use get_local_issues_tool with lat/lon for location-based issue searches
- Use get_location_info_tool to tell users where they are based on coordinates

RESPONSE GUIDELINES:
- Be concise, helpful, and professional
- Always use tools to get accurate, real-time information
- If a tool fails, explain what went wrong
- Format responses clearly with relevant details
- If you don't know something, admit it politely and suggest alternatives"""

class LangChainAgent:
    """LangChain-based agent with better reasoning and tool orchestration"""
    
    def __init__(self):
        self.llm = get_llm()
        self.tools = [
            get_weather_tool,
            get_local_news_tool,
            get_india_news_tool,
            get_local_issues_tool,
            get_location_info_tool,
            track_report_tool
        ]
        
        # Create the agent using LangChain/LangGraph
        if not USE_CREATE_AGENT:
            raise ImportError("LangChain agent creation not available")
        
        # Create the agent - it will handle tool binding automatically
        if AGENT_PARAM_NAME == "prompt":
            # create_react_agent uses 'prompt' parameter
            self.agent = create_agent(
                model=self.llm,
                tools=self.tools,
                prompt=SYSTEM_PROMPT,
                debug=False
            )
        else:
            # create_agent uses 'system_prompt' parameter
            self.agent = create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=SYSTEM_PROMPT,
                debug=False
            )
    
    def process_message(
        self, 
        message: str, 
        user_location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message using LangChain agent
        
        Args:
            message: User's message
            user_location: Optional dict with 'lat' and 'lon' keys
        
        Returns:
            Response dict with success, data, message, and intent
        """
        try:
            # Prepare messages with location context
            message_content = message
            
            # Add location context if available
            location_context = ""
            if user_location:
                lat = user_location.get("lat")
                lon = user_location.get("lon")
                if lat and lon:
                    # Get location name for better context
                    try:
                        location_result = reverse_geocode(lat, lon)
                        if location_result.get("success"):
                            data = location_result["data"]
                            city = data.get("city", "")
                            state = data.get("state", "")
                            location_name = f"{city}, {state}" if state else city
                            location_context = f"\n\n[USER LOCATION CONTEXT: The user is currently at {location_name}. Their coordinates are lat={lat}, lon={lon}. When they say 'here', 'my area', 'my location', 'current location', or 'in my area', you MUST use these coordinates (lat={lat}, lon={lon}) in the tool calls. Do NOT try to geocode or search for the location name - use the coordinates directly.]"
                        else:
                            location_context = f"\n\n[USER LOCATION CONTEXT: The user's coordinates are lat={lat}, lon={lon}. When they say 'here', 'my area', 'my location', or 'current location', you MUST use these coordinates (lat={lat}, lon={lon}) in the tool calls.]"
                    except:
                        location_context = f"\n\n[USER LOCATION CONTEXT: The user's coordinates are lat={lat}, lon={lon}. When they say 'here', 'my area', 'my location', or 'current location', you MUST use these coordinates (lat={lat}, lon={lon}) in the tool calls.]"
            
            # Add location context to message
            if location_context:
                message_content = message + location_context
            
            messages = [HumanMessage(content=message_content)]
            
            # Invoke the agent
            result = self.agent.invoke({"messages": messages})
            
            # Extract the final response - get the last AI message
            messages_list = result.get("messages", [])
            response_text = ""
            
            # Find the last AI message (non-tool message)
            for msg in reversed(messages_list):
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
                    response_text = msg.content
                    break
            
            if not response_text:
                # Fallback: use last message
                if messages_list:
                    last_msg = messages_list[-1]
                    if hasattr(last_msg, 'content'):
                        response_text = last_msg.content
                    else:
                        response_text = str(last_msg)
            
            # Detect intent from response or tool usage
            intent = "general"
            if "weather" in message.lower() or "temperature" in message.lower():
                intent = "weather"
            elif "news" in message.lower():
                intent = "news"
            elif "issue" in message.lower() or "problem" in message.lower():
                intent = "local_issues"
            elif "report" in message.lower():
                intent = "reports"
            
            return {
                "success": True,
                "data": {"response": response_text},
                "message": "Response generated successfully",
                "intent": intent,
                "model": OLLAMA_MODEL
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"LangChain agent error: {error_trace}")
            
            # Fallback to error response
            return {
                "success": False,
                "error": str(e),
                "message": f"Error processing message: {str(e)}",
                "intent": "general"
            }

