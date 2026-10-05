#!/usr/bin/env python3
"""Test script to verify Gemini API connection"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key and model
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL")

print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Missing'}")
print(f"🤖 Model: {model_name}")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

# Configure the API
genai.configure(api_key=api_key)

print("\n🧪 Testing Gemini API...")
print("=" * 50)

try:
    # Create model
    model = genai.GenerativeModel(model_name)
    
    # Test generation
    response = model.generate_content("Hello! Can you tell me what you are in one sentence?")
    
    if response and response.text:
        print("✅ Gemini API is working!")
        print(f"📝 Response: {response.text.strip()}")
    else:
        print("❌ No response received from Gemini API")
        
except Exception as e:
    print(f"❌ Error testing Gemini API: {e}")
    print(f"   Error type: {type(e).__name__}")
    
    # Check if it's a model not found error
    if "404" in str(e) or "not found" in str(e).lower():
        print("\n💡 The model name might be incorrect.")
        print("   Run 'python list_gemini_models.py' to see available models")
    
print("\n" + "=" * 50)
