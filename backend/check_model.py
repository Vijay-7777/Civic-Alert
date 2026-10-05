#!/usr/bin/env python3
"""
Quick script to check if the configured Ollama model is installed.
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_command(cmd):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_ollama_installed():
    """Check if Ollama is installed"""
    success, stdout, stderr = run_command("ollama --version")
    return success

def list_installed_models():
    """List currently installed Ollama models"""
    success, stdout, stderr = run_command("ollama list")
    if success:
        return stdout
    return ""

def check_model_installed(model_name):
    """Check if a specific model is installed"""
    models_output = list_installed_models()
    # Check if model name appears in the list
    # Ollama list format: MODEL_NAME    SIZE    MODIFIED
    lines = models_output.split('\n')
    for line in lines:
        if model_name in line:
            return True
    return False

def main():
    print("=" * 60)
    print("🔍 Checking Ollama Model Installation")
    print("=" * 60)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("\n❌ Ollama is not installed or not in PATH.")
        print("Please install Ollama from: https://ollama.ai")
        sys.exit(1)
    
    print("\n✅ Ollama is installed!")
    
    # Get configured model
    configured_model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
    print(f"\n📋 Configured model: {configured_model}")
    
    # List all installed models
    print("\n📦 Installed models:")
    models = list_installed_models()
    if models:
        print(models)
    else:
        print("  (No models installed)")
    
    # Check if configured model is installed
    print("\n" + "=" * 60)
    if check_model_installed(configured_model):
        print(f"✅ Model '{configured_model}' is INSTALLED!")
        print("\nYou're all set! The model is ready to use.")
    else:
        print(f"❌ Model '{configured_model}' is NOT INSTALLED!")
        print("\n📥 To install it, run:")
        print(f"   ollama pull {configured_model}")
        print("\nOr use the upgrade script:")
        print("   python backend/upgrade_model.py")
        print("\n💡 Alternative models you can use:")
        print("   - ollama pull gemma3:1b")
        print("   - ollama pull llama3.2:3b")
        print("   - ollama pull phi3:mini")
        print("   - ollama pull qwen3:4b")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()

