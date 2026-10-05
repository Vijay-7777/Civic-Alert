import sys
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent import Agent
from app.tools import track_report
from app.db import fetch_report

def test_track_report(report_id):
    """Test the entire report tracking flow"""
    print(f"\n{'='*50}")
    print(f"Testing report tracking for ID: {report_id}")
    print(f"{'='*50}")
    
    # Test 1: Direct fetch from database
    print("\n[TEST 1] Testing direct database fetch...")
    try:
        report = fetch_report(report_id)
        if report:
            print("✅ Success: Report found in database")
            print(f"    Report ID: {report.get('reportId')}")
            print(f"    Title: {report.get('title')}")
            print(f"    Status: {report.get('status')}")
        else:
            print(f"❌ Error: No report found with ID: {report_id}")
    except Exception as e:
        print(f"❌ Error in fetch_report: {str(e)}")
    
    # Test 2: Track report using track_report function
    print("\n[TEST 2] Testing track_report function...")
    try:
        result = track_report(report_id)
        if result.get('success'):
            print("✅ Success: track_report returned successfully")
            report_data = result.get('data', {})
            print(f"    Report ID: {report_data.get('reportId')}")
            print(f"    Title: {report_data.get('title')}")
            print(f"    Status: {report_data.get('status')}")
        else:
            print(f"❌ Error in track_report: {result.get('error')}")
            print(f"    Message: {result.get('message')}")
            if 'suggestions' in result:
                print("    Suggestions:")
                for i, suggestion in enumerate(result['suggestions'], 1):
                    print(f"    {i}. {suggestion}")
    except Exception as e:
        print(f"❌ Unexpected error in track_report: {str(e)}")
    
    # Test 3: Test through the agent
    print("\n[TEST 3] Testing through Agent...")
    try:
        agent = Agent()
        
        # Test with different message formats
        test_messages = [
            f"Track report {report_id}",
            f"Status of report {report_id}",
            f"What's the status of report {report_id}?",
            report_id  # Just the ID
        ]
        
        for i, msg in enumerate(test_messages, 1):
            print(f"\n  Test 3.{i}: {msg}")
            try:
                response = agent.process_message(msg)
                if response.get('success'):
                    print(f"  ✅ Success: {response.get('message')}")
                    if 'data' in response and 'response' in response['data']:
                        print(f"  Response: {response['data']['response']}")
                else:
                    print(f"  ❌ Error: {response.get('error')}")
                    print(f"  Message: {response.get('message')}")
            except Exception as e:
                print(f"  ❌ Error processing message: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error in Agent test: {str(e)}")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    # Test with a known report ID
    test_report_id = "4d14ffa4138d4bd0"  # Replace with an actual report ID from your database
    
    if len(sys.argv) > 1:
        test_report_id = sys.argv[1]
    
    test_track_report(test_report_id)
    
    # Test with a non-existent ID
    # test_track_report("nonexistent123")
