#!/usr/bin/env python3
"""Test agent with local news"""

from app.agent import Agent

agent = Agent()

message = "Show me local news"
user_location = {"lat": 29.3938, "lon": 79.4538}

print("\n📰 Testing agent with local news...")
print("=" * 50)

try:
    response = agent.process_message(message, user_location)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
