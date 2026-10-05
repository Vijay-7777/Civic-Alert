#!/usr/bin/env python3
"""Test LLM call directly"""

from app.agent import Agent

# Initialize agent
agent = Agent()

print(f"🤖 Agent initialized:")
print(f"  Use Gemini: {agent.use_gemini}")
print(f"  Gemini Model: {agent.gemini_model}")

# Test LLM call directly
print("\n🧪 Testing LLM call directly...")
print("=" * 50)

try:
    response = agent.call_llm(
        prompt="Hi",
        system_prompt="You are a helpful Civic Alert assistant. Be concise and helpful."
    )
    
    print("✅ LLM Response:")
    print(f"  {response}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 50)
