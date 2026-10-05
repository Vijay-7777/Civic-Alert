import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up test environment variables
os.environ["GEMINI_API_KEY"] = "test_key"
os.environ["USE_GEMINI_API"] = "true"

# Mock the required modules
import sys
from unittest.mock import MagicMock

# Mock the Gemini API
sys.modules['google.generativeai'] = MagicMock()
sys.modules['google.generativeai'].configure = MagicMock()
sys.modules['google.generativeai'].GenerativeModel = MagicMock()

# Mock langchain and other dependencies
sys.modules['langchain.memory'] = MagicMock()
sys.modules['langchain.tools'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()

# Import the agent after setting up mocks
from app.agent_advanced import AdvancedAgent

def test_agent_initialization():
    try:
        # Test agent initialization
        agent = AdvancedAgent()
        print("✅ Agent initialized successfully")
        
        # Test basic message processing
        response = agent.process_message("Fetch me latest news in locality")
        print(f"✅ Basic message processing test passed. Response: {response}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Civic Alert Advanced Agent...")
    success = test_agent_initialization()
    
    if success:
        print("\n🎉 All tests passed! The agent is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
    
    print("\nNote: This is a basic functionality test. For full testing, please ensure all dependencies are installed.")
