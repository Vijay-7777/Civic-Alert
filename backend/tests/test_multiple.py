#!/usr/bin/env python3
"""Test multiple message types"""

from app.agent import Agent

# Initialize agent
agent = Agent()

# Test messages
test_messages = [
    ("Hi", {"lat": 29.3938, "lon": 79.4538}),
    ("What's the weather like?", {"lat": 29.3938, "lon": 79.4538}),
    ("Show me local news", {"lat": 29.3938, "lon": 79.4538}),
    ("Help me report a crime", {"lat": 29.3938, "lon": 79.4538}),
    ("Thank you", {"lat": 29.3938, "lon": 79.4538})
]

print("\n🧪 Testing multiple message types...")
print("=" * 50)

for message, location in test_messages:
    print(f"\n📝 Message: '{message}'")
    try:
        response = agent.process_message(message, location)
        if response.get('success'):
            intent = response.get('intent', 'unknown')
            
            # Handle different response formats
            if intent == 'weather' and 'temperature' in response.get('data', {}):
                # Weather data format
                data = response.get('data', {})
                resp_text = f"Weather in {data.get('city', 'Unknown')}: {data.get('temperature', 'N/A')}°C, {data.get('description', 'N/A')}"
            elif intent == 'news' and isinstance(response.get('data'), list):
                # News data format (list of articles)
                articles = response.get('data', [])
                if articles:
                    resp_text = f"Found {len(articles)} news articles: {articles[0].get('title', 'No title')[:50]}..."
                else:
                    resp_text = "No news articles found"
            else:
                # Standard response format
                resp_text = response.get('data', {}).get('response', 'No response')
            
            print(f"  ✅ Intent: {intent}")
            print(f"  📄 Response: {resp_text[:100]}...")
        else:
            print(f"  ❌ Failed: {response}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 50)
