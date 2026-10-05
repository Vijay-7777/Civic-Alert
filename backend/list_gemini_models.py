#!/usr/bin/env python3
"""Script to list available Gemini models"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

# Configure the API
genai.configure(api_key=api_key)

print("🔍 Listing available Gemini models...")
print("=" * 50)

try:
    # List all models
    models = list(genai.list_models())
    
    print(f"Found {len(models)} models:")
    print()
    
    # Filter for models that support generateContent
    generate_models = []
    for model in models:
        if "generateContent" in model.supported_generation_methods:
            generate_models.append(model)
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:100]}...")
            print(f"   Methods: {', '.join(model.supported_generation_methods)}")
            print()
    
    if not generate_models:
        print("❌ No models found that support generateContent")
    else:
        print(f"\n📋 Found {len(generate_models)} models that support generateContent")
        
        # Find the best model to use
        flash_models = [m for m in generate_models if "flash" in m.name.lower()]
        if flash_models:
            print(f"\n🎯 Recommended Flash models:")
            for model in flash_models:
                print(f"   - {model.name}")
        
        # Find 2.0 models
        two_models = [m for m in generate_models if "2.0" in m.name.lower()]
        if two_models:
            print(f"\n🚀 Gemini 2.0 models:")
            for model in two_models:
                print(f"   - {model.name}")
        
        # Also check for 1.5 models
        one_five_models = [m for m in generate_models if "1.5" in m.name.lower()]
        if one_five_models:
            print(f"\n📚 Gemini 1.5 models:")
            for model in one_five_models:
                print(f"   - {model.name}")

except Exception as e:
    print(f"❌ Error listing models: {e}")
    print(f"   Error type: {type(e).__name__}")
    
print("\n" + "=" * 50)
print("🔧 To fix the model name, update GEMINI_MODEL in .env to one of the above models")
