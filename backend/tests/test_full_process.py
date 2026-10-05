#!/usr/bin/env python3
"""Test the full process_message with detailed output"""

from app.agent import Agent
import json

# Initialize agent
agent = Agent()

# Test with full process
print("\n🔍 Testing full process_message...")
print("=" * 50)

message = "Hi"
user_location = {"lat": 29.3938, "lon": 79.4538}

try:
    response = agent.process_message(
        message=message,
        user_location=user_location
    )
    
    print("✅ Full Response:")
    print(json.dumps(response, indent=2))
    
    if response.get('success') and 'data' in response and 'response' in response['data']:
        print(f"\n📝 Actual Response Text: '{response['data']['response']}'")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
