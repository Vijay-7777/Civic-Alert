#!/usr/bin/env python3
"""Debug the process_message flow"""

from app.agent import Agent

# Initialize agent
agent = Agent()

# Test with debugging
print("\n🔍 Debugging process_message flow...")
print("=" * 50)

message = "Hi"
user_location = {"lat": 29.3938, "lon": 79.4538}

# Step 1: Detect intent
intent = agent.detect_intent(message)
print(f"1. Detected intent: '{intent}'")

# Step 2: Extract coordinates
coordinates = agent.extract_coordinates(message)
print(f"2. Extracted coordinates: {coordinates}")

# Step 3: Check user location
if not coordinates and user_location:
    coordinates = (user_location.get("lat"), user_location.get("lon"))
    print(f"3. Using user location: {coordinates}")

# Step 4: Check if it's a general_chat intent
if intent == "general_chat":
    print("4. Intent is 'general_chat', preparing LLM call...")
    
    # Get location context
    location_context = ""
    if coordinates:
        lat, lon = coordinates
        from app.tools import reverse_geocode
        location_result = reverse_geocode(lat, lon)
        if location_result["success"]:
            city = location_result["data"]["city"]
            state = location_result["data"]["state"]
            location_context = f"User's location: {city}, {state}. "
    
    # Create prompt
    user_prompt = f"{location_context}User says: '{message}'"
    system_prompt = """You are a helpful Civic Alert assistant. You help users with:
- Crime reporting and tracking
- Local news and weather information  
- Community issues and concerns
- General safety and security advice

Analyze the user's query and determine if it needs:
1. Weather information (mention weather, temperature, climate, rain)
2. News information (mention news, headlines, articles)
3. Location-based issues (mention local, nearby, area, neighborhood)
4. Report help (mention report, file, submit, track)
5. General conversation (greetings, help, thanks)

Respond naturally and helpfully. If they need specific services, offer to help with those."""
    
    print(f"5. System prompt: {system_prompt[:100]}...")
    print(f"6. User prompt: {user_prompt}")
    
    # Call LLM
    try:
        llm_response = agent.call_llm(user_prompt, system_prompt)
        print(f"7. LLM response: '{llm_response}'")
        
        # Check if it's an error
        if llm_response.startswith("LLM Error") or llm_response.startswith("I'm having trouble") or llm_response.startswith("I'm unable to connect"):
            print("8. LLM returned error, using fallback")
            fallback_response = agent._get_fallback_response(message, user_location)
            print(f"9. Fallback response: '{fallback_response}'")
        else:
            print("8. LLM response is good")
            
    except Exception as e:
        print(f"8. Error calling LLM: {e}")
elif intent == "general":
    print("4. Intent is 'general' (old path)")

print("\n" + "=" * 50)
