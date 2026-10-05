#!/usr/bin/env python3
"""Check what models are available via Ollama API"""

import requests
import json

try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print("Models available via API:")
        print("=" * 60)
        for model in data.get("models", []):
            print(f"  - {model.get('name', 'Unknown')}")
        print("=" * 60)
        
        # Check if gemma3:1b is in the list
        model_names = [m.get('name') for m in data.get("models", [])]
        if "gemma3:1b" in model_names:
            print("\n✅ gemma3:1b is available via API")
        else:
            print("\n❌ gemma3:1b is NOT available via API")
            print("Available gemma models:")
            for name in model_names:
                if "gemma" in name.lower():
                    print(f"  - {name}")
            print("\n💡 You may need to:")
            print("   1. Restart Ollama service")
            print("   2. Use one of the available models")
            print("   3. Re-pull the model: ollama pull gemma3:1b")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {str(e)}")

