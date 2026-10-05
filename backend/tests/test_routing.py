#!/usr/bin/env python3
"""Test all routing intents to demonstrate proper tool usage"""

from app.agent import Agent

agent = Agent()

test_cases = [
    {
        "message": "What's the weather like?",
        "location": {"lat": 29.3938, "lon": 79.4538},
        "expected_intent": "weather",
        "expected_tool": "Weather API",
        "description": "Routes to weather tool"
    },
    {
        "message": "Show me local news",
        "location": {"lat": 29.3938, "lon": 79.4538},
        "expected_intent": "news",
        "expected_tool": "Web Search (DuckDuckGo/NewsAPI)",
        "description": "Routes to web search for local news"
    },
    {
        "message": "What are the local issues in my area?",
        "location": {"lat": 29.3938, "lon": 79.4538},
        "expected_intent": "local_issues",
        "expected_tool": "Database (Qdrant/SQLite)",
        "description": "Routes to database for local issues"
    },
    {
        "message": "Help me report a crime",
        "location": {"lat": 29.3938, "lon": 79.4538},
        "expected_intent": "reports",
        "expected_tool": "Report Management System",
        "description": "Routes to report handling"
    },
    {
        "message": "Hi there!",
        "location": {"lat": 29.3938, "lon": 79.4538},
        "expected_intent": "general",
        "expected_tool": "LLM (Gemini) for conversation",
        "description": "Routes to LLM for general chat"
    }
]

print("\n🧭 Testing Intent Routing to Tools")
print("=" * 60)

all_passed = True
for test in test_cases:
    print(f"\n📝 Test: {test['description']}")
    print(f"   Message: '{test['message']}'")
    
    try:
        response = agent.process_message(test['message'], test['location'])
        
        if response.get('success'):
            intent = response.get('intent', 'unknown')
            
            if intent == test['expected_intent']:
                print(f"   ✅ Intent: {intent} (correct)")
                print(f"   🔧 Routes to: {test['expected_tool']}")
                
                # Show sample of response
                if intent == 'weather':
                    data = response.get('data', {})
                    print(f"   📄 Sample: {data.get('city', 'N/A')} - {data.get('temperature', 'N/A')}°C")
                elif intent == 'news':
                    articles = response.get('data', [])
                    print(f"   📄 Sample: Found {len(articles)} articles")
                elif intent == 'local_issues':
                    issues = response.get('data', [])
                    print(f"   📄 Sample: Found {len(issues)} issues")
                else:
                    resp = response.get('data', {}).get('response', '')
                    print(f"   📄 Sample: {resp[:50]}...")
            else:
                print(f"   ❌ Intent mismatch: expected {test['expected_intent']}, got {intent}")
                all_passed = False
        else:
            print(f"   ❌ Failed: {response.get('error', 'Unknown error')}")
            all_passed = False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("✅ All routing tests passed!")
else:
    print("❌ Some tests failed")
