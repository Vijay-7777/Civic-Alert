#!/usr/bin/env python3
"""
Test Ollama API directly with the correct format.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"

print("Testing Ollama API...")
print(f"URL: {OLLAMA_URL}")
print(f"Model: {MODEL}\n")

# Test with the format we're using
payload = {
    "model": MODEL,
    "prompt": "Say hello",
    "stream": False
}

print("Request payload:")
print(json.dumps(payload, indent=2))
print("\nSending request...")

try:
    response = requests.post(OLLAMA_URL, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success! Response: {data.get('response', '')[:100]}")
    else:
        print(f"\n❌ Error: {response.text}")
except Exception as e:
    print(f"\n❌ Exception: {str(e)}")

