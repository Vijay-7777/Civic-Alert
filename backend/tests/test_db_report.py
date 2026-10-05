import sqlite3
from pathlib import Path
import sys

def check_database():
    """Check database connection and report table"""
    try:
        # Try both possible database paths
        db_paths = [
            Path('frontend/data/crime_lens.db'),
            Path('data/crime_lens.db'),
            Path('backend/frontend/data/crime_lens.db'),
            Path('backend/data/crime_lens.db')
        ]
        
        db_path = None
        for path in db_paths:
            if path.exists():
                db_path = path
                break
                
        if not db_path:
            return {"success": False, "error": f"Database not found in any of: {[str(p) for p in db_paths]}"}
            
        print(f"Found database at: {db_path.absolute()}")
        
        # Check connection and tables
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if Report table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Report'")
        if not cursor.fetchone():
            return {"success": False, "error": "Report table not found in database"}
            
        # Count reports
        cursor.execute("SELECT COUNT(*) as count FROM Report")
        count = cursor.fetchone()['count']
        
        # Get first few reports
        cursor.execute("SELECT id, reportId, title, status FROM Report LIMIT 5")
        reports = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "db_path": str(db_path.absolute()),
            "report_count": count,
            "sample_reports": reports
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    finally:
        if 'conn' in locals():
            conn.close()

def lookup_report(report_id):
    """Lookup a specific report by ID"""
    try:
        result = check_database()
        if not result.get('success'):
            return result
            
        db_path = result['db_path']
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Try exact match with reportId
        cursor.execute(
            "SELECT * FROM Report WHERE reportId = ? COLLATE NOCASE", 
            (report_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                "success": True,
                "found_by": "reportId",
                "report": dict(row)
            }
            
        # Try with ID if numeric
        if report_id.isdigit():
            cursor.execute("SELECT * FROM Report WHERE id = ?", (int(report_id),))
            row = cursor.fetchone()
            if row:
                return {
                    "success": True,
                    "found_by": "id",
                    "report": dict(row)
                }
        
        # If not found, get all report IDs for debugging
        cursor.execute("SELECT id, reportId, title, status FROM Report LIMIT 10")
        all_reports = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": False,
            "error": "Report not found",
            "tried_ids": [report_id],
            "available_reports": all_reports
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # First check database connection
    print("=== Checking database connection ===")
    db_check = check_database()
    print("\nDatabase check result:")
    print(f"Success: {db_check.get('success')}")
    
    if not db_check.get('success'):
        print(f"Error: {db_check.get('error')}")
        if 'traceback' in db_check:
            print("\nTraceback:")
            print(db_check['traceback'])
        sys.exit(1)
    
    print(f"Database path: {db_check['db_path']}")
    print(f"Total reports: {db_check['report_count']}")
    print("\nSample reports:")
    for report in db_check.get('sample_reports', []):
        print(f"- ID: {report.get('id')}, ReportID: {report.get('reportId')}, "
              f"Title: {report.get('title')}, Status: {report.get('status')}")
    
    # Test report lookup
    test_id = "4d14ffa4138d4bd0"
    print(f"\n=== Looking up report with ID: {test_id} ===")
    result = lookup_report(test_id)
    
    if result.get('success'):
        print(f"\n✅ Found report by {result['found_by']}:")
        report = result['report']
        for key, value in report.items():
            print(f"{key}: {value}")
    else:
        print(f"\n❌ Report not found")
        print(f"Error: {result.get('error')}")
        
        if 'available_reports' in result and result['available_reports']:
            print("\nAvailable reports (first 10):")
            for r in result['available_reports']:
                print(f"- ID: {r.get('id')}, ReportID: {r.get('reportId')}, "
                      f"Title: {r.get('title')}, Status: {r.get('status')}")
        
        if 'traceback' in result:
            print("\nTraceback:")
            print(result['traceback'])
    
    print("\nTest complete.")
