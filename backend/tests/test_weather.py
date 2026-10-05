#!/usr/bin/env python3
"""Test weather function directly"""

from app.tools import get_weather

print("\n🌤️ Testing weather function...")
print("=" * 50)

try:
    result = get_weather(29.3938, 79.4538)
    print("Weather result:")
    import json
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
