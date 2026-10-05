import sys
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tools import track_report

def test_report_tracking(report_id):
    print(f"\n{'='*50}")
    print(f"Testing report tracking for ID: {report_id}")
    print(f"{'='*50}")
    
    # Test the track_report function
    print("\n[TEST] Testing track_report function...")
    try:
        result = track_report(report_id)
        
        if result.get('success'):
            print("✅ Success: track_report returned successfully")
            report_data = result.get('data', {})
            print(f"    Report ID: {report_data.get('reportId')}")
            print(f"    Title: {report_data.get('title')}")
            print(f"    Status: {report_data.get('status')}")
            print(f"    Created: {report_data.get('createdAt')}")
            print(f"    Department: {report_data.get('department', {}).get('name')}")
        else:
            print(f"❌ Error in track_report: {result.get('error')}")
            print(f"    Message: {result.get('message')}")
            if 'suggestions' in result:
                print("    Suggestions:")
                for i, suggestion in enumerate(result['suggestions'], 1):
                    print(f"    {i}. {suggestion}")
    except Exception as e:
        print(f"❌ Unexpected error in track_report: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    # Test with the known report ID
    test_report_id = "4d14ffa4138d4bd0"
    
    if len(sys.argv) > 1:
        test_report_id = sys.argv[1]
    
    test_report_tracking(test_report_id)
