#!/usr/bin/env python3
"""
Test if Ollama service is running and accessible.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")

def test_ollama_connection():
    """Test if Ollama is running and accessible"""
    print("=" * 60)
    print("🔍 Testing Ollama Connection")
    print("=" * 60)
    
    print(f"\n📍 Ollama URL: {OLLAMA_URL}")
    print(f"🤖 Model: {OLLAMA_MODEL}")
    
    # Test 1: Check if Ollama service is running
    print("\n1️⃣ Testing Ollama service connection...")
    try:
        # Try to access Ollama API
        health_url = OLLAMA_URL.replace("/api/generate", "/api/tags")
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Ollama service is running!")
        else:
            print(f"   ⚠️  Ollama responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to Ollama service!")
        print("   💡 Make sure Ollama is running:")
        print("      - On Windows: Check if Ollama is running in the background")
        print("      - Or start it: ollama serve")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Test 2: Check if model is available
    print("\n2️⃣ Testing model availability...")
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": "test",
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Model '{OLLAMA_MODEL}' is accessible and working!")
            data = response.json()
            if "response" in data:
                print(f"   📝 Test response: {data['response'][:50]}...")
            return True
        elif response.status_code == 404:
            print(f"   ❌ Model '{OLLAMA_MODEL}' not found!")
            print(f"   💡 Install it with: ollama pull {OLLAMA_MODEL}")
            return False
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing model: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_ollama_connection()
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! Ollama is ready to use.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)

