#!/usr/bin/env python3
"""Test the agent directly"""

from app.agent import Agent

# Initialize agent
agent = Agent()

print(f"🤖 Agent initialized:")
print(f"  Use Gemini: {agent.use_gemini}")
print(f"  Gemini Model: {agent.gemini_model}")

# Test with a simple message
print("\n🧪 Testing agent with simple message...")
print("=" * 50)

try:
    response = agent.process_message(
        message="Hi",
        user_location={"lat": 29.3938, "lon": 79.4538}
    )
    
    print("✅ Agent response:")
    print(f"  Success: {response['success']}")
    print(f"  Intent: {response['intent']}")
    if 'model' in response:
        print(f"  Model: {response['model']}")
    if 'data' in response and 'response' in response['data']:
        print(f"  Response: {response['data']['response']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 50)
