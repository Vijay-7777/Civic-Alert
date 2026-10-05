"""Test script for the Advanced Agent."""

import sys
import os
import json
from pathlib import Path

# Add the parent directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent_advanced import AdvancedAgent

def test_agent():
    """Test the advanced agent with various queries."""
    print("🚀 Testing Advanced Agent...\n")
    
    # Initialize the agent
    agent = AdvancedAgent()
    
    # Test cases
    test_cases = [
        {"message": "What's the weather like?", "location": {"lat": 28.6139, "lon": 77.2090}},  # Delhi
        {"message": "Show me local news", "location": {"lat": 18.5204, "lon": 73.8567}},  # Pune
        {"message": "What's happening in India?"},
        {"message": "Track report 12345"},
        {"message": "What are the local issues?", "location": {"lat": 12.9716, "lon": 77.5946}},  # Bangalore
        {"message": "Tell me more about the second news item"}  # Tests conversation memory
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔹 Test {i}: {test['message']}")
        print(f"   Location: {test.get('location', 'None')}")
        
        response = agent.process_message(
            message=test["message"],
            user_location=test.get("location")
        )
        
        print(f"\n   Response:")
        print(f"   Success: {response['success']}")
        print(f"   Intent: {response.get('intent', 'N/A')}")
        print(f"   Model: {response.get('model', 'N/A')}")
        print("\n   Message:")
        print(f"   {response['message']}\n")
        print("-" * 80)

if __name__ == "__main__":
    test_agent()
