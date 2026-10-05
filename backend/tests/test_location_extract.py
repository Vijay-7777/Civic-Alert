#!/usr/bin/env python3
"""Test location extraction"""

import re
from app.agent import Agent

agent = Agent()

message = "What's the weather like?"
print(f"\n🔍 Testing location extraction for: '{message}'")
print("=" * 50)

# Test pattern matching
message_lower = message.lower()
patterns = [
    r'weather\s+(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\?|$|,|\s+and)',
    r'weather\s+([a-zA-Z\s]+?)(?:\?|$)',
    r'news\s+(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\?|$|,|\s+and)',
    r'news\s+([a-zA-Z\s]+?)(?:\?|$)',
    r'issues?\s+(?:in|at|for|near)\s+([a-zA-Z\s]+?)(?:\?|$|,|\s+and)',
]

print("Pattern matching results:")
for i, pattern in enumerate(patterns, 1):
    match = re.search(pattern, message_lower)
    if match:
        location = match.group(1).strip()
        print(f"  Pattern {i}: '{location}'")
    else:
        print(f"  Pattern {i}: No match")

# Test LLM extraction
print("\nLLM extraction:")
try:
    prompt = f"Extract the location/city name from this query. If there's a location mentioned, return ONLY the location name, nothing else. If no location is mentioned, return 'NONE'.\n\nQuery: {message}\n\nLocation:"
    llm_response = agent.call_llm(prompt, "You are a location extraction assistant. Extract city/location names from queries.")
    location = llm_response.strip()
    print(f"  LLM response: '{location}'")
    print(f"  Valid location: {location.upper() != 'NONE' and len(location) > 2}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 50)
