#!/usr/bin/env python3
"""
Switch between Ollama and Gemini API for Civic Alert
"""

import os
from pathlib import Path

# Get the backend directory
backend_dir = Path(__file__).parent
env_file = backend_dir / ".env"

def switch_to_ollama():
    """Switch back to Ollama"""
    print("🔄 Switching back to Ollama...")
    
    if not env_file.exists():
        print("❌ .env file not found.")
        return
    
    # Read current .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update the configuration
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('USE_GEMINI_API='):
            updated_lines.append('USE_GEMINI_API=false')
        else:
            updated_lines.append(line)
    
    # Write back to .env
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print("✅ Switched back to Ollama successfully!")
    print("📝 The chatbot will now use Ollama instead of Gemini API.")

def switch_to_gemini():
    """Switch to Gemini API"""
    print("🔄 Switching to Gemini API...")
    
    if not env_file.exists():
        print("❌ .env file not found.")
        return
    
    # Check if API key is configured
    with open(env_file, 'r') as f:
        content = f.read()
    
    if 'GEMINI_API_KEY=your_gemini_api_key_here' in content or 'GEMINI_API_KEY=' not in content:
        print("❌ Gemini API key not configured. Please run: python setup_gemini.py")
        return
    
    # Update the configuration
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('USE_GEMINI_API='):
            updated_lines.append('USE_GEMINI_API=true')
        else:
            updated_lines.append(line)
    
    # Write back to .env
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print("✅ Switched to Gemini API successfully!")
    print("📝 The chatbot will now use Gemini API instead of Ollama.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "ollama":
            switch_to_ollama()
        elif sys.argv[1] == "gemini":
            switch_to_gemini()
        else:
            print("Usage: python switch_provider.py [ollama|gemini]")
    else:
        print("Current configuration:")
        with open(env_file, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if 'USE_GEMINI_API=' in line:
                    provider = "Gemini API" if "true" in line.lower() else "Ollama"
                    print(f"  Provider: {provider}")
                    break
        print("\nUsage: python switch_provider.py [ollama|gemini]")
