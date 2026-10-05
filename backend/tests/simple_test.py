from app.agent_advanced import advanced_agent

def test_agent():
    # Test with a simple query
    response = advanced_agent.process_message(
        message="What's the weather like in Delhi?",
        user_location={"lat": 28.6139, "lon": 77.2090}
    )
    
    print("\n=== Test Result ===")
    print(f"Success: {response['success']}")
    print(f"Response: {response['message']}")
    print(f"Model: {response.get('model', 'N/A')}")

if __name__ == "__main__":
    test_agent()
