import requests
import json
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_track_report(report_id):
    url = "http://localhost:8000/agent"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "message": f"Track report {report_id}",
        "user_location": {
            "latitude": 28.6139,
            "longitude": 77.2090
        }
    }

    try:
        logger.info(f"Sending request to track report {report_id}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            logger.info("✅ Report found and processed successfully")
            print("\n" + "="*50)
            print("REPORT DETAILS:")
            print("="*50)
            print(result.get("data", {}).get("response", "No details available"))
            print("="*50 + "\n")
        else:
            logger.error(f"❌ Error: {result.get('error')}")
            logger.error(f"Message: {result.get('message')}")
            if "suggestions" in result:
                logger.error("Suggestions:")
                for i, suggestion in enumerate(result["suggestions"], 1):
                    logger.error(f"  {i}. {suggestion}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                logger.error(f"Response content: {e.response.text}")
            except:
                pass
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_report_id = "4d14ffa4138d4bd0"
    if len(sys.argv) > 1:
        test_report_id = sys.argv[1]
    test_track_report(test_report_id)
