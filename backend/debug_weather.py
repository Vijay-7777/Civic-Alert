#!/usr/bin/env python3
"""Debug weather intent processing"""

from app.agent import Agent

# Initialize agent
agent = Agent()

message = "What's the weather like?"
user_location = {"lat": 29.3938, "lon": 79.4538}

print("\n🌤️ Debugging weather intent...")
print("=" * 50)

# Step 1: Detect intent
intent = agent.detect_intent(message)
print(f"1. Detected intent: '{intent}'")

# Step 2: Extract coordinates
coordinates = agent.extract_coordinates(message)
print(f"2. Extracted coordinates: {coordinates}")

# Step 3: Use user location if no coordinates
if not coordinates and user_location:
    coordinates = (user_location.get("lat"), user_location.get("lon"))
    print(f"3. Using user location: {coordinates}")

# Step 4: Check if it's weather intent
if intent == "weather":
    print("4. Processing weather intent...")
    
    # Check if user wants weather "here" or "in my area"
    message_lower = message.lower()
    use_user_location = any(word in message_lower for word in ["here", "my area", "my location", "current location", "where i am"])
    print(f"5. Use user location: {use_user_location}")
    
    # Try to extract location name from message
    location_name = None
    if not use_user_location:
        location_name = agent.extract_location_name(message)
        print(f"6. Extracted location name: {location_name}")
    
    # Priority: user coordinates > extracted location name > error
    if coordinates and (use_user_location or not location_name):
        print("7. Using user coordinates for weather...")
        lat, lon = coordinates
        from app.tools import get_weather
        result = get_weather(lat, lon)
        result["intent"] = "weather"
        print(f"8. Weather result: {result}")
        # Format the response
        if result.get("success"):
            data = result["data"]
            formatted_response = f"🌡️ Current weather in {data['city']}, {data['country']}:\n"
            formatted_response += f"📊 Temperature: {data['temperature']}°C (feels like {data['feels_like']}°C)\n"
            formatted_response += f"💧 Humidity: {data['humidity']}%\n"
            formatted_response += f"☁️ Conditions: {data['description']}"
            print(f"9. Formatted response: {formatted_response[:100]}...")

print("\n" + "=" * 50)
