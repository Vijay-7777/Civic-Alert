"""Integration test for the Civic Alert agent."""

import os
import sys
import asyncio
import json
from typing import Dict, Any

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent_advanced import AdvancedAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_agent():
    """Test the agent with sample queries."""
    print("🚀 Initializing Civic Alert Agent...")
    agent = AdvancedAgent()
    
    # Test location (Nainital, India)
    test_location = {"lat": 29.3919, "lon": 79.4541}
    
    # Test queries
    test_queries = [
        "What's the weather like?",
        "What are the latest news headlines?",
        "I want to report a pothole on Mall Road",
        "Track report #12345",
        "What are the local issues in my area?"
    ]
    
    for query in test_queries:
        print(f"\n🧪 Testing query: {query}")
        print("-" * 50)
        
        try:
            # Process the message
            response = agent.process_message(query, test_location)
            
            # Print the response
            print(f"✅ Response (Intent: {response.get('intent', 'unknown')}):")
            print(response.get('message', 'No response message'))
            
            # Print any data if available
            if response.get('data'):
                print("\n📊 Response data:")
                if isinstance(response['data'], dict) or isinstance(response['data'], list):
                    print(json.dumps(response['data'], indent=2))
                else:
                    print(str(response['data']))
                
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
        await asyncio.sleep(1)  # Add a small delay between queries

if __name__ == "__main__":
    print("🔍 Starting Civic Alert Agent Tests...")
    asyncio.run(test_agent())
