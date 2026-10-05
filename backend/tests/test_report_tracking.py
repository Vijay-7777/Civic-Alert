import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tools import track_report
from app.db import fetch_report

def test_report_lookup(report_id):
    print(f"\n=== Testing report lookup for ID: {report_id} ===")
    
    # Test fetch_report directly
    print("\n--- Testing fetch_report ---")
    try:
        report = fetch_report(report_id)
        if report:
            print("✅ fetch_report SUCCESS")
            print(f"Report ID: {report.get('reportId')}")
            print(f"Title: {report.get('title')}")
            print(f"Status: {report.get('status')}")
        else:
            print("❌ fetch_report returned None")
    except Exception as e:
        print(f"❌ fetch_report ERROR: {e}")
    
    # Test track_report
    print("\n--- Testing track_report ---")
    try:
        result = track_report(report_id)
        if result.get('success'):
            print("✅ track_report SUCCESS")
            print(f"Message: {result.get('message')}")
            print(f"Report ID: {result.get('data', {}).get('reportId')}")
            print(f"Status: {result.get('data', {}).get('status')}")
        else:
            print(f"❌ track_report FAILED: {result.get('error')}")
            print(f"Message: {result.get('message')}")
    except Exception as e:
        import traceback
        print(f"❌ track_report ERROR: {e}")
        print("Traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    # Test with a known report ID from the database
    test_id = "4d14ffa4138d4bd0"
    test_report_lookup(test_id)
    
    # Test with a non-existent ID
    test_report_lookup("nonexistent123")
    
    # Test with an empty ID
    test_report_lookup("")
