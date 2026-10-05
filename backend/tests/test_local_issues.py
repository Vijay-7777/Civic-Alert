#!/usr/bin/env python3
"""Test local issues intent"""

from app.agent import Agent

agent = Agent()

message = "What are the local issues in my area?"
user_location = {"lat": 29.3938, "lon": 79.4538}

print("\n🚨 Testing local issues...")
print("=" * 50)

try:
    response = agent.process_message(message, user_location)
    print(f"Response: {response}")
    
    if response.get('success'):
        intent = response.get('intent', 'unknown')
        print(f"\n✅ Intent: {intent}")
        
        if intent == 'local_issues':
            data = response.get('data', {})
            if isinstance(data, list):
                print(f"📄 Found {len(data)} local issues")
                for issue in data[:3]:  # Show first 3
                    print(f"  - {issue.get('title', 'No title')}")
            else:
                print(f"📄 Response: {data}")
    else:
        print(f"❌ Failed: {response}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
