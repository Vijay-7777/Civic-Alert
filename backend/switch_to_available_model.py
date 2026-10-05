#!/usr/bin/env python3
"""
Automatically switch to an available model if the configured one isn't available.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_available_models():
    """Get list of models available via API"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m.get('name') for m in data.get("models", [])]
    except:
        pass
    return []

def main():
    print("=" * 60)
    print("🔄 Switching to Available Model")
    print("=" * 60)
    
    # Get available models
    available = get_available_models()
    if not available:
        print("\n❌ Cannot connect to Ollama API")
        print("Make sure Ollama is running")
        return
    
    print(f"\n📋 Available models: {', '.join(available)}")
    
    # Preferred models in order
    preferred = ["gemma3:1b", "llama3.2:3b", "phi3:mini", "qwen3:4b", "qwen2.5:3b"]
    
    # Find best available model
    best_model = None
    for model in preferred:
        if model in available:
            best_model = model
            break
    
    if not best_model:
        best_model = available[0]  # Use first available
    
    print(f"\n✅ Selected model: {best_model}")
    
    # Update .env file
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    updated = False
    
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("OLLAMA_MODEL"):
                new_lines.append(f"OLLAMA_MODEL={best_model}\n")
                found = True
                updated = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"OLLAMA_MODEL={best_model}\n")
            updated = True
        
        with open(env_file, "w") as f:
            f.writelines(new_lines)
    else:
        # Create .env file
        with open(env_file, "w") as f:
            f.write(f"OLLAMA_MODEL={best_model}\n")
        updated = True
    
    if updated:
        print(f"\n✅ Updated .env file to use: {best_model}")
        print("\n📌 Next steps:")
        print("   1. Restart your backend server")
        print("   2. Test the model with a query")
    else:
        print(f"\n💡 To use {best_model}, set in .env:")
        print(f"   OLLAMA_MODEL={best_model}")

if __name__ == "__main__":
    main()

