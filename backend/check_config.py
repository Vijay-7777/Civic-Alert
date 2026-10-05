#!/usr/bin/env python3
"""Check configuration values"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Configuration Check")
print("=" * 50)

# Check all relevant config
print(f"GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
print(f"GEMINI_MODEL: {os.getenv('GEMINI_MODEL')}")
print(f"USE_GEMINI_API: {os.getenv('USE_GEMINI_API')}")

# Import and check config module
try:
    from app.config import GEMINI_API_KEY, GEMINI_MODEL, USE_GEMINI_API
    print("\n📋 From app.config:")
    print(f"GEMINI_API_KEY: {'✅ Set' if GEMINI_API_KEY else '❌ Missing'}")
    print(f"GEMINI_MODEL: {GEMINI_MODEL}")
    print(f"USE_GEMINI_API: {USE_GEMINI_API}")
except Exception as e:
    print(f"❌ Error importing config: {e}")

# Test agent initialization
try:
    from app.agent import Agent
    agent = Agent()
    print(f"\n🤖 Agent initialized:")
    print(f"  Use Gemini: {agent.use_gemini}")
    print(f"  Gemini Model: {agent.gemini_model}")
    print(f"  Ollama Model: {agent.model}")
except Exception as e:
    print(f"❌ Error initializing agent: {e}")

print("\n" + "=" * 50)
