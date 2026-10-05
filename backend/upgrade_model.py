#!/usr/bin/env python3
"""
Helper script to upgrade the LLM model for better reasoning capabilities.
This script helps you install and configure a better model under 3B parameters.
"""

import subprocess
import sys
import os

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

def install_model(model_name):
    """Install a model using Ollama"""
    print(f"\n📥 Installing {model_name}...")
    print("This may take a few minutes depending on your internet connection...")
    
    success, stdout, stderr = run_command(f"ollama pull {model_name}")
    
    if success:
        print(f"✅ Successfully installed {model_name}!")
        return True
    else:
        print(f"❌ Failed to install {model_name}")
        print(f"Error: {stderr}")
        return False

def main():
    print("=" * 60)
    print("🚀 LLM Model Upgrade Helper")
    print("=" * 60)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("\n❌ Ollama is not installed or not in PATH.")
        print("Please install Ollama from: https://ollama.ai")
        sys.exit(1)
    
    print("\n✅ Ollama is installed!")
    
    # Show current models
    print("\n📋 Currently installed models:")
    models = list_installed_models()
    print(models)
    
    # Recommended models
    print("\n" + "=" * 60)
    print("Recommended Models Under 3B Parameters:")
    print("=" * 60)
    print("\n1. qwen2.5:3b (RECOMMENDED) ⭐")
    print("   - 3B parameters")
    print("   - Excellent reasoning capabilities")
    print("   - Multilingual support")
    print("   - Best balance of performance and size")
    
    print("\n2. llama3.2:3b")
    print("   - 3B parameters")
    print("   - Good reasoning")
    print("   - Fast inference")
    
    print("\n3. phi3:mini")
    print("   - 3.8B parameters (slightly over 3B)")
    print("   - Excellent reasoning (rivals GPT-3.5)")
    print("   - MIT license")
    
    # Ask user which model to install
    print("\n" + "=" * 60)
    choice = input("\nWhich model would you like to install? (1/2/3) [1]: ").strip() or "1"
    
    model_map = {
        "1": "qwen2.5:3b",
        "2": "llama3.2:3b",
        "3": "phi3:mini"
    }
    
    if choice not in model_map:
        print("Invalid choice. Using default: qwen2.5:3b")
        choice = "1"
    
    model_name = model_map[choice]
    
    # Check if already installed
    if model_name in models:
        print(f"\n✅ {model_name} is already installed!")
        use_it = input(f"Do you want to use {model_name} as the default model? (y/n) [y]: ").strip().lower() or "y"
    else:
        # Install the model
        if install_model(model_name):
            use_it = "y"
        else:
            print("\n❌ Installation failed. Please try again.")
            sys.exit(1)
    
    if use_it == "y":
        # Update .env file or show instructions
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        
        if os.path.exists(env_file):
            # Read current .env
            with open(env_file, "r") as f:
                content = f.read()
            
            # Update or add OLLAMA_MODEL
            if "OLLAMA_MODEL" in content:
                lines = content.split("\n")
                new_lines = []
                for line in lines:
                    if line.startswith("OLLAMA_MODEL"):
                        new_lines.append(f"OLLAMA_MODEL={model_name}")
                    else:
                        new_lines.append(line)
                content = "\n".join(new_lines)
            else:
                content += f"\nOLLAMA_MODEL={model_name}\n"
            
            # Write back
            with open(env_file, "w") as f:
                f.write(content)
            
            print(f"\n✅ Updated .env file to use {model_name}")
        else:
            print(f"\n📝 To use {model_name}, add this to your .env file:")
            print(f"   OLLAMA_MODEL={model_name}")
            print("\nOr set it as an environment variable:")
            print(f"   export OLLAMA_MODEL={model_name}")
        
        print("\n" + "=" * 60)
        print("✅ Model upgrade complete!")
        print("=" * 60)
        print("\n📌 Next steps:")
        print("1. Restart your backend server")
        print("2. Test the new model with a query")
        print("3. Check the model name in chat responses")
        print("\n💡 The system will automatically use the correct prompt format")
        print("   for the selected model (Qwen, Llama, or Phi-3).")

if __name__ == "__main__":
    main()

