#!/usr/bin/env python3
"""Debug weather flow in process_message"""

from app.agent import Agent

agent = Agent()

message = "What's the weather like?"
user_location = {"lat": 29.3938, "lon": 79.4538}

print("\n🌤️ Debugging weather flow...")
print("=" * 50)

# Full process_message
response = agent.process_message(message, user_location)
print(f"Full response: {response}")

# Check if it's going to general_chat instead
if response.get('intent') == 'general':
    print("\n⚠️ Intent was 'general', checking why...")
    
    # Check detect_intent
    detected_intent = agent.detect_intent(message)
    print(f"Detect intent result: '{detected_intent}'")
    
    # Check if coordinates are being extracted
    coords = agent.extract_coordinates(message)
    print(f"Extracted coordinates: {coords}")
    
    # Check location name extraction
    location_name = agent.extract_location_name(message)
    print(f"Extracted location name: '{location_name}'")

print("\n" + "=" * 50)
