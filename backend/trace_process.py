#!/usr/bin/env python3
"""Trace through the actual process_message method"""

from app.agent import Agent
import json

# Initialize agent
agent = Agent()

# Test with detailed trace
print("\n🔍 Tracing process_message method...")
print("=" * 50)

message = "Hi"
user_location = {"lat": 29.3938, "lon": 79.4538}

# Step 1: Get intent
intent = agent.detect_intent(message)
print(f"1. Initial intent detection: '{intent}'")

# Step 2: Get coordinates
coordinates = agent.extract_coordinates(message)
if not coordinates and user_location:
    coordinates = (user_location.get("lat"), user_location.get("lon"))
print(f"2. Coordinates: {coordinates}")

# Step 3: Check if general_chat
if intent == "general_chat":
    print("3. Handling general_chat intent...")
    
    # The analysis prompt
    system_prompt = """You are a helpful Civic Alert assistant. You help users with:
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
Otherwise, provide a helpful, concise response."""
    
    analysis_prompt = f"User query: {message}\n\nWhat type of query is this? Respond with only one word: weather, news, issues, reports, or general."
    print(f"4. Analysis prompt: {analysis_prompt}")
    
    intent_analysis = agent.call_llm(analysis_prompt, system_prompt).strip().lower()
    print(f"5. Intent analysis result: '{intent_analysis}'")
    
    # This is where it goes wrong - it's using the analysis result as the final response
    if "weather" not in intent_analysis and "news" not in intent_analysis and "issues" not in intent_analysis:
        print("6. Not a specific intent, proceeding to general response...")
        
        user_prompt = f"User asked: {message}\n\nProvide a helpful, concise response:"
        print(f"7. User prompt: {user_prompt}")
        
        llm_response = agent.call_llm(user_prompt, system_prompt)
        print(f"8. LLM response: '{llm_response}'")

print("\n" + "=" * 50)
