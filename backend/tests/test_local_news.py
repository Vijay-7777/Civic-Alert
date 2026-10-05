#!/usr/bin/env python3
"""Test local news function directly"""

from app.tools import get_local_news, reverse_geocode

print("\n📰 Testing local news function...")
print("=" * 50)

# Test reverse_geocode first
print("1. Testing reverse_geocode...")
try:
    result = reverse_geocode(29.3938, 79.4538)
    print(f"   Result: {result}")
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

# Test get_local_news
print("\n2. Testing get_local_news...")
try:
    result = get_local_news("Nainital", 29.3938, 79.4538, try_neighbors=True)
    print(f"   Result: {result}")
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
