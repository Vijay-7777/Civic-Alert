import requests
import json
import re
from typing import Dict, Any, Optional, Tuple
from .config import (
    OLLAMA_URL, OLLAMA_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL, USE_GEMINI_API,
    NEWS_API_KEY, WEATHER_API_KEY, OPENWEATHER_API_KEY,
    QDRANT_URL, QDRANT_COLLECTION, EMBEDDING_MODEL
)
from .tools import (
    get_india_news, search_news_duckduckgo, search_news_google,
    get_local_news, get_weather, rag_local_issues, fetch_report,
    reverse_geocode, geocode_location
)

class Agent:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = OLLAMA_MODEL
        self.use_gemini = USE_GEMINI_API
        self.gemini_api_key = GEMINI_API_KEY
        self.gemini_model = GEMINI_MODEL
    
    def call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """Call LLM API - either Gemini or Ollama based on configuration"""
        if self.use_gemini and self.gemini_api_key:
            return self._call_gemini_api(prompt, system_prompt)
        else:
            return self._call_ollama_api(prompt, system_prompt)
    
    def _call_gemini_api(self, prompt: str, system_prompt: str = None) -> str:
        """Call Gemini API for LLM inference"""
        try:
            import google.generativeai as genai
            
            # Configure Gemini API
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.gemini_model)
            
            # Prepare the prompt with system instruction if provided
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            else:
                full_prompt = f"You are a helpful Civic Alert assistant. Be concise and helpful.\n\nUser: {prompt}\n\nAssistant:"
            
            # Generate response
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except ImportError:
            return "Google Generative AI library not installed. Please run: pip install google-generativeai"
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "permission" in error_msg:
                return "Gemini API key is invalid or missing. Please check your GEMINI_API_KEY configuration."
            elif "quota" in error_msg or "rate limit" in error_msg:
                return "Gemini API quota exceeded. Please try again later or check your billing."
            else:
                return f"Gemini API error: {str(e)}"
    
    def _call_ollama_api(self, prompt: str, system_prompt: str = None) -> str:
        """Call Ollama API for LLM inference with better prompting"""
        try:
            # Detect model type and use appropriate prompt format
            model_lower = self.model.lower()
            
            # Qwen models use ChatML format
            if "qwen" in model_lower:
                if system_prompt:
                    full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
                else:
                    full_prompt = f"<|im_start|>system\nYou are a helpful Civic Alert assistant. Be concise and helpful.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
            # Llama models use their own format
            elif "llama" in model_lower or "phi" in model_lower:
                if system_prompt:
                    full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
                else:
                    full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a helpful Civic Alert assistant. Be concise and helpful.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            # Default format (for Gemma and others)
            else:
                if system_prompt:
                    full_prompt = f"<|system|>{system_prompt}<|end|>\n<|user|>{prompt}<|end|>\n<|assistant|>"
                else:
                    full_prompt = f"You are a helpful Civic Alert assistant. Be concise and helpful.\n<|user|>{prompt}<|end|>\n<|assistant|>"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,  # Balanced temperature for better reasoning
                    "num_predict": 1024,  # Increased token limit for better responses
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "top_k": 40  # Better sampling for reasoning tasks
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            elif response.status_code == 404:
                # Model not found - provide helpful installation instructions
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", response.text)
                if "not found" in error_msg.lower():
                    install_cmd = f"ollama pull {self.model}"
                    return f"I'm having trouble with the AI model right now. The model '{self.model}' is not installed.\n\nTo install it, run:\n```bash\n{install_cmd}\n```\n\nOr use the upgrade script: `python backend/upgrade_model.py`"
                return f"Model error: {error_msg}"
            else:
                return f"Service temporarily unavailable. Please try again later."
        except requests.exceptions.ConnectionError:
            return "I'm unable to connect to the AI service right now. Please make sure Ollama is running."
        except requests.exceptions.Timeout:
            return "The AI service is taking too long to respond. Please try again."
        except Exception as e:
            return f"I encountered an error: {str(e)}. Please try again or contact support."
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message with improved report tracking detection"""
        message_lower = message.lower().strip()
        
        # Handle simple confirmations - these should be treated as general chat but with better fallback
        if re.match(r'^(yes|yeah|yep|yup|sure|ok|okay|alright|fine)$', message_lower):
            return "confirmation"
        
        # Check for report tracking patterns first (most specific)
        # Match patterns like:
        # - track report 4d14ffa4138d4bd0
        # - status of report 4d14ffa4138d4bd0
        # - 4d14ffa4138d4bd0
        if (re.search(r'track\s+report\s+[a-f0-9-]+', message_lower) or  # track report 4d14ffa4138d4bd0
            re.search(r'report\s+[a-f0-9-]+\s+track', message_lower) or  # report 4d14ffa4138d4bd0 track
            re.search(r'[a-f0-9]{8,}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}', message_lower) or  # UUID with hyphens
            re.search(r'[a-f0-9]{16,}', message_lower) or  # Compact UUID
            re.search(r'report\s*#?\s*[a-f0-9-]+', message_lower)):  # report#4d14ffa4138d4bd0
            return "track_report"
            
        # India news (check for "for india", "india news", etc.)
        elif re.search(r'\b(?:for\s+)?india\s+news\b|\bnews\s+(?:for\s+)?india\b|\bshow\s+me\s+india\s+news\b|^india$|^for\s+india$', message_lower):
            return "india_news"
        # Local news (check before general news)
        elif re.search(r'\blocal\s+news\b|\bnews\s+here\b|\bnews\s+near\b|\bshow\s+me\s+local\s+news\b|\bgive\s+me\s+local\s+news\b', message_lower):
            return "local_news"
        # Weather
        elif re.search(r'\bweather\b|\btemperature\b|\brain\b|\bclimate\b|\bwhat\'?s?\s+the\s+weather\b', message_lower):
            return "weather"
        # Local issues
        elif re.search(r'\bissues?\s+near\s+me\b|\blocal\s+issues?\b|\bproblems?\s+near\b|\bissues?\s+here\b', message_lower):
            return "local_issues"
        # Location query
        elif re.search(r'\blocation\b|\barea\b|\bwhere\s+am\s+i\b|\bwhat\'?s?\s+my\s+location\b|\bwhat\'?s?\s+my\s+area\b', message_lower):
            return "location_query"
        # General reports
        elif re.search(r'\breport\b|\bcomplaint\b|\bsubmit\s+(a\s+)?report\b|\bfile\s+(a\s+)?complaint\b', message_lower):
            return "reports"
        else:
            return "general_chat"
    
    def extract_coordinates(self, message: str) -> Optional[tuple]:
        """Extract coordinates from message if present"""
        # Look for latitude/longitude patterns
        lat_lon_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        match = re.search(lat_lon_pattern, message)
        
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except ValueError:
                pass
        return None
    
    def extract_location_name(self, message: str) -> Optional[str]:
        """Extract location/city name from message using LLM"""
        message_lower = message.lower()
        
        # Common patterns for location extraction
        patterns = [
            r'weather\s+(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\?|$|,|\s+and)',
            r'weather\s+(?:like|what\'?s|how\s+is)\s+(?:in|at|for)?\s*([a-zA-Z\s]+?)(?:\?|$)',
            r'news\s+(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\?|$|,|\s+and)',
            r'news\s+([a-zA-Z\s]+?)(?:\?|$)',
            r'issues?\s+(?:in|at|for|near)\s+([a-zA-Z\s]+?)(?:\?|$|,|\s+and)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                location = match.group(1).strip()
                # Filter out common words
                location = re.sub(r'\b(?:the|a|an|in|at|for|near|my|local|current)\b', '', location).strip()
                if location and len(location) > 2:
                    return location
        
        # Try using LLM to extract location if pattern matching fails
        try:
            prompt = f"Extract the location/city name from this query. If there's a location mentioned, return ONLY the location name, nothing else. If no location is mentioned, return 'NONE'.\n\nQuery: {message}\n\nLocation:"
            llm_response = self.call_llm(prompt, "You are a location extraction assistant. Extract city/location names from queries.")
            location = llm_response.strip()
            if location and location.upper() != "NONE" and len(location) > 2:
                return location
        except:
            pass
        
        return None
    
    def extract_report_id(self, message: str) -> Optional[str]:
        """Extract report ID from message. Supports both numeric and UUID-style IDs."""
        # First, try to find a UUID pattern (32 hex digits, with or without hyphens)
        uuid_pattern = r'[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}'
        match = re.search(uuid_pattern, message)
        if match:
            # Remove any hyphens for consistency
            return match.group(0).replace('-', '').lower()
        
        # Then try to find a compact UUID (16+ hex digits)
        compact_uuid_pattern = r'[0-9a-fA-F]{16,}'
        match = re.search(compact_uuid_pattern, message)
        if match:
            return match.group(0).lower()
        
        # Finally, try to find a numeric ID
        numeric_match = re.search(r'\b(\d+)\b', message)
        if numeric_match:
            return numeric_match.group(1)
            
        return None
    
    def _get_fallback_response(self, message: str, user_location: Optional[Dict] = None) -> str:
        """Provide fallback responses when LLM is unavailable"""
        message_lower = message.lower()
        
        # Location-related queries
        if re.search(r'\blocation\b|\barea\b|\bwhere\b|\bplace\b|\bcity\b', message_lower):
            if user_location:
                lat = user_location.get("lat")
                lon = user_location.get("lon")
                if lat and lon:
                    location_result = reverse_geocode(lat, lon)
                    if location_result.get("success"):
                        city = location_result["data"].get("city", "your area")
                        state = location_result["data"].get("state", "")
                        location_str = f"{city}, {state}" if state else city
                        return f"I can help you find your location! Based on your coordinates, you're in {location_str}. You can also ask me about local news, weather, or issues in your area."
            return "I can help you find your location! Please make sure location services are enabled, or you can ask me about local news, weather, or issues in your area."
        
        # General greeting
        if re.search(r'\bhi\b|\bhello\b|\bhey\b|\bgreetings\b', message_lower):
            return "Hello! I'm your Civic Alert assistant. I can help you with reports, news, weather, and local issues. How can I assist you today?"
        
        # Help requests
        if re.search(r'\bhelp\b|\bwhat\s+can\s+you\b|\bhow\s+can\s+you\b', message_lower):
            return "I can help you with:\n- Submitting and tracking crime reports\n- Getting local news and weather\n- Finding local issues in your area\n- General safety and security information\n\nWhat would you like to know?"
        
        # Default fallback
        return "I understand your question, but I'm having trouble with the AI service right now. You can still:\n- Ask about weather (I'll use your location)\n- Request local news\n- Search for local issues\n- Submit or track reports\n\nPlease try one of these specific actions, or contact support if you need further assistance."
    
    def process_message(self, message: str, user_location: Optional[Dict] = None) -> Dict[str, Any]:
        """Main agent processing function"""
        intent = self.detect_intent(message)
        coordinates = self.extract_coordinates(message)
        
        # Use user location if no coordinates in message
        if not coordinates and user_location:
            coordinates = (user_location.get("lat"), user_location.get("lon"))
        
        try:
            if intent == "india_news":
                result = get_india_news()
                result["intent"] = "news"
                return result
            
            elif intent == "local_news":
                # Check if user wants news "here" or "in my area"
                message_lower = message.lower()
                use_user_location = any(word in message_lower for word in ["here", "my area", "my location", "current location", "where i am", "really tell my area"])
                
                # Try to extract location name from message (only if not using user location)
                location_name = None
                if not use_user_location:
                    location_name = self.extract_location_name(message)
                
                # Priority: user coordinates > extracted location name > error
                if coordinates and (use_user_location or not location_name):
                    # Use user's current location
                    lat, lon = coordinates
                    location_result = reverse_geocode(lat, lon)
                    if location_result["success"]:
                        city = location_result["data"]["city"]
                        # Also try state for broader search
                        state = location_result["data"].get("state", "")
                        search_query = f"{city} {state}" if state else city
                        result = get_local_news(search_query, lat, lon, try_neighbors=True)
                        result["intent"] = "news"
                        return result
                    else:
                        return {"success": False, "error": "Could not determine location", "message": "Failed to get location for local news. Please make sure location services are enabled.", "intent": "news"}
                elif location_name:
                    # User specified a location, try to geocode it to get coordinates for neighbor search
                    geo_result = geocode_location(location_name)
                    lat, lon = None, None
                    if geo_result.get("success"):
                        lat = geo_result["data"]["lat"]
                        lon = geo_result["data"]["lon"]
                    result = get_local_news(location_name, lat, lon, try_neighbors=True)
                    result["intent"] = "news"
                    return result
                elif coordinates:
                    # Fallback to user coordinates
                    lat, lon = coordinates
                    location_result = reverse_geocode(lat, lon)
                    if location_result["success"]:
                        city = location_result["data"]["city"]
                        result = get_local_news(city, lat, lon, try_neighbors=True)
                        result["intent"] = "news"
                        return result
                    else:
                        return {"success": False, "error": "Could not determine location", "message": "Failed to get location for local news. Please make sure location services are enabled.", "intent": "news"}
                else:
                    return {"success": False, "error": "Location required", "message": "Please provide a city name or enable location services for local news", "intent": "news"}
            
            elif intent == "weather":
                # Check if user wants weather "here" or "in my area"
                message_lower = message.lower()
                use_user_location = any(word in message_lower for word in ["here", "my area", "my location", "current location", "where i am"])
                
                # Try to extract location name from message (only if not using user location)
                location_name = None
                if not use_user_location:
                    location_name = self.extract_location_name(message)
                
                # Priority: user coordinates > extracted location name > error
                if coordinates and (use_user_location or not location_name):
                    # Use user's current location
                    lat, lon = coordinates
                    result = get_weather(lat, lon)
                    result["intent"] = "weather"
                    return result
                elif location_name:
                    # User specified a location name, geocode it
                    geo_result = geocode_location(location_name)
                    if geo_result.get("success"):
                        lat = geo_result["data"]["lat"]
                        lon = geo_result["data"]["lon"]
                        result = get_weather(lat, lon)
                        result["intent"] = "weather"
                        return result
                    else:
                        return {"success": False, "error": "Location not found", "message": f"Could not find weather for '{location_name}'. Please provide a valid city name or enable location services.", "intent": "weather"}
                elif coordinates:
                    # Fallback to user coordinates even if location name extraction failed
                    lat, lon = coordinates
                    result = get_weather(lat, lon)
                    result["intent"] = "weather"
                    return result
                else:
                    return {"success": False, "error": "Location required", "message": "Please provide a city name or enable location services for weather information", "intent": "weather"}
            
            elif intent == "local_issues":
                if coordinates:
                    lat, lon = coordinates
                    result = rag_local_issues(message, lat, lon)
                    result["intent"] = "local_issues"
                    return result
                else:
                    result = rag_local_issues(message)
                    result["intent"] = "local_issues"
                    return result
            
            # Handle track report intent - also check if message contains a report ID pattern
            elif intent == "track_report" or any(re.search(r'[a-f0-9-]{8,}', message.lower()) for _ in [0]):
                # Extract report ID using the improved extractor
                report_id = self.extract_report_id(message)
                if report_id:
                    try:
                        from .tools import track_report
                        print(f"[DEBUG] Processing track report request for ID: {report_id}")
                        result = track_report(report_id)
                        
                        if result.get("success"):
                            report_data = result.get("data", {})
                            print(f"[DEBUG] Found report data: {report_data}")
                            
                            # Format the response for the chat using the correct field names
                            status = str(report_data.get("status", "Not available")).title()
                            created_at = report_data.get("createdAt", "Not available")
                            report_type = str(report_data.get("type", "Not available")).upper()

                            raw_location = report_data.get("location")
                            if isinstance(raw_location, str):
                                location_name = raw_location or "Not available"
                            elif isinstance(raw_location, dict):
                                location_name = (
                                    raw_location.get("name")
                                    or raw_location.get("address")
                                    or raw_location.get("formatted")
                                    or raw_location.get("location")
                                    or "Not available"
                                )
                            else:
                                location_name = "Not available"
                            report_id_display = report_data.get("reportId", report_id)
                            
                            response = {
                                "success": True,
                                "data": {
                                    "response": (
                                        f"📋 **Report #{report_id_display}**\n\n"
                                        f"🔹 **Status:** {status}\n"
                                        f"🔹 **Type:** {report_type}\n"
                                        f"🔹 **Title:** {report_data.get('title', 'No title')}\n"
                                        f"🔹 **Location:** {location_name}\n"
                                        f"🔹 **Created:** {created_at}\n\n"
                                        f"Please let me know if you need any more details about this report."
                                    ),
                                    "report_data": report_data
                                },
                                "message": result.get("message", "Report details retrieved"),
                                "intent": "reports"
                            }
                            print(f"[DEBUG] Sending response: {response}")
                            return response
                        else:
                            # Use the error message and suggestions from track_report
                            error_msg = result.get("message", f"Could not find report #{report_id}")
                            suggestions = result.get("suggestions", [
                                "Make sure you entered the correct report ID",
                                "Check for any typos in the report ID"
                            ])
                            
                            response = {
                                "success": False,
                                "error": result.get("error", "report_not_found"),
                                "message": error_msg,
                                "suggestions": suggestions,
                                "intent": "reports"
                            }
                            print(f"[DEBUG] Report not found: {response}")
                            return response
                        
                    except Exception as e:
                        import traceback
                        error_trace = traceback.format_exc()
                        print(f"[ERROR] Error in track_report handler: {error_trace}")
                        
                        error_response = {
                            "success": False,
                            "error": "server_error",
                            "message": "An error occurred while processing your request. Please try again later.",
                            "details": {
                                "error_type": type(e).__name__,
                                "error_message": str(e)
                            },
                            "intent": "reports"
                        }
                        print(f"[ERROR] Error response: {error_response}")
                        return error_response
                else:
                    error_response = {
                        "success": False,
                        "error": "no_report_id",
                        "message": (
                            "I couldn't find a valid report ID in your message. "
                            "Please provide a report ID in one of these formats:\n\n"
                            "• Track report 4d14ffa4138d4bd0\n"
                            "• Status of report 4d14ffa4-138d-4bd0-8f1a-5c9b2c7d8e9f\n"
                            "• 4d14ffa4138d4bd0"
                        ),
                        "suggestions": [
                            "Make sure to include a valid report ID",
                            "Check for any typos in the report ID"
                        ]
                    }
                    print(f"[DEBUG] No valid report ID found: {error_response}")
                    return error_response
            
            elif intent == "reports":
                # General report-related queries
                return {
                    "success": True,
                    "data": {"response": "I can help you with reports! You can submit a new report or track existing ones. What would you like to do?"},
                    "message": "Report assistance provided",
                    "intent": "reports"
                }
            
            elif intent == "confirmation":
                # Handle simple confirmations - if user confirms after a news prompt, show India news
                # This is the most common use case: "yes" after "Would you like India news instead?"
                result = get_india_news()
                result["intent"] = "news"
                return result
            
            elif intent == "location_query":
                # Handle location queries directly without LLM
                if user_location:
                    lat = user_location.get("lat")
                    lon = user_location.get("lon")
                    if lat and lon:
                        location_result = reverse_geocode(lat, lon)
                        if location_result.get("success"):
                            city = location_result["data"].get("city", "your area")
                            state = location_result["data"].get("state", "")
                            country = location_result["data"].get("country", "")
                            location_str = f"{city}"
                            if state:
                                location_str += f", {state}"
                            if country:
                                location_str += f", {country}"
                            return {
                                "success": True,
                                "data": {"response": f"Based on your coordinates, you're currently in **{location_str}**. I can help you with local news, weather, or issues in this area!"},
                                "message": "Location information provided",
                                "intent": "general"
                            }
                return {
                    "success": True,
                    "data": {"response": "I need your location to tell you where you are. Please make sure location services are enabled, or you can ask me about local news, weather, or issues in your area."},
                    "message": "Location not available",
                    "intent": "general"
                }
            
            else:  # general_chat
                # Use LLM to understand the query and potentially route to appropriate tools
                analysis_system_prompt = """You are a helpful Civic Alert assistant. You help users with:
- Crime reporting and tracking
- Local news and weather information  
- Community issues and concerns
- General safety and security advice

Analyze the user's query and determine if it needs:
1. Weather information (mention weather, temperature, climate, rain)
2. News information (mention news, headlines, articles)
3. Local issues (mention issues, problems, complaints in an area)
4. Report submission/tracking (mention report, complaint, submit)
5. General information or conversation

If the query is about weather, news, or issues, respond with just the intent type (weather/news/issues/reports/general).
Otherwise, respond with 'conversation'."""
                
                # First, let LLM analyze the intent
                analysis_prompt = f"User query: {message}\n\nWhat type of query is this? Respond with only one word: weather, news, issues, reports, conversation."
                intent_analysis = self.call_llm(analysis_prompt, analysis_system_prompt).strip().lower()
                
                # Check if LLM detected a specific intent that we should handle
                if "weather" in intent_analysis and "weather" not in message.lower():
                    # LLM detected weather intent, try to extract location and get weather
                    location_name = self.extract_location_name(message)
                    if location_name or coordinates:
                        if location_name:
                            geo_result = geocode_location(location_name)
                            if geo_result.get("success"):
                                lat = geo_result["data"]["lat"]
                                lon = geo_result["data"]["lon"]
                                result = get_weather(lat, lon)
                                result["intent"] = "weather"
                                return result
                        elif coordinates:
                            lat, lon = coordinates
                            result = get_weather(lat, lon)
                            result["intent"] = "weather"
                            return result
                
                # Use LLM for general response with a clear, friendly prompt
                response_system_prompt = """You are a helpful and friendly Civic Alert assistant. You help users with:
- Crime reporting and tracking
- Local news and weather information  
- Community issues and concerns
- General safety and security advice

Be friendly, helpful, and concise. If the user just says hi or hello, greet them warmly and briefly mention what you can help with. Always provide natural, conversational responses."""
                
                # Get location context if available
                location_context = ""
                if coordinates:
                    lat, lon = coordinates
                    location_result = reverse_geocode(lat, lon)
                    if location_result["success"]:
                        city = location_result["data"]["city"]
                        state = location_result["data"]["state"]
                        location_context = f"The user is in {city}, {state}. "
                
                user_prompt = f"{location_context}User says: '{message}'"
                llm_response = self.call_llm(user_prompt, response_system_prompt)
                
                # Check if LLM response indicates an error
                if llm_response.startswith("LLM Error") or llm_response.startswith("I'm having trouble") or llm_response.startswith("I'm unable to connect"):
                    # Provide a fallback response based on the query
                    fallback_response = self._get_fallback_response(message, user_location)
                    return {
                        "success": True,
                        "data": {"response": fallback_response},
                        "message": "Fallback response provided",
                        "intent": "general"
                    }
                
                return {
                    "success": True,
                    "data": {"response": llm_response},
                    "message": "LLM response generated",
                    "intent": "general"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Agent processing failed"
            }
