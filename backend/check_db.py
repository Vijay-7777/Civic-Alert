import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

def get_db_path() -> Optional[Path]:
    """Find the database file"""
    possible_paths = [
        Path("frontend/data/crime_lens.db"),
        Path("data/crime_lens.db"),
        Path("backend/frontend/data/crime_lens.db"),
        Path("backend/data/crime_lens.db"),
        Path(__file__).parent.parent / "frontend" / "data" / "crime_lens.db"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.absolute()
    return None

def check_database() -> Dict[str, Any]:
    """Check database connection and schema"""
    db_path = get_db_path()
    if not db_path:
        return {"success": False, "error": "Database file not found"}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check Report table structure
        report_columns = []
        if 'Report' in tables:
            cursor.execute("PRAGMA table_info(Report)")
            report_columns = [dict(zip(['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'], row)) 
                            for row in cursor.fetchall()]
        
        # Count reports
        report_count = 0
        sample_reports = []
        if 'Report' in tables:
            cursor.execute("SELECT COUNT(*) FROM Report")
            report_count = cursor.fetchone()[0]
            
            # Get sample reports
            cursor.execute("SELECT reportId, title, status, createdAt FROM Report LIMIT 5")
            sample_reports = [dict(zip(['reportId', 'title', 'status', 'createdAt'], row)) 
                            for row in cursor.fetchall()]
        
        return {
            "success": True,
            "db_path": str(db_path),
            "tables": tables,
            "report_columns": report_columns,
            "report_count": report_count,
            "sample_reports": sample_reports
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "db_path": str(db_path) if 'db_path' in locals() else None
        }
    finally:
        if 'conn' in locals():
            conn.close()

def test_report_lookup(report_id: str) -> Dict[str, Any]:
    """Test looking up a specific report"""
    db_path = get_db_path()
    if not db_path:
        return {"success": False, "error": "Database file not found"}
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Try exact match with reportId
        cursor.execute("SELECT * FROM Report WHERE reportId = ?", (report_id,))
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
        all_reports = [dict(zip(['id', 'reportId', 'title', 'status'], row)) 
                      for row in cursor.fetchall()]
        
        return {
            "success": False,
            "error": "Report not found",
            "tried_ids": [report_id],
            "available_reports": all_reports
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== Database Check ===")
    db_check = check_database()
    
    if not db_check.get('success'):
        print(f"❌ Error: {db_check.get('error')}")
        if 'db_path' in db_check and db_check['db_path']:
            print(f"Database path: {db_check['db_path']}")
        exit(1)
    
    print(f"✅ Database found at: {db_check['db_path']}")
    print(f"\n=== Database Schema ===")
    print(f"Tables: {', '.join(db_check['tables']) if db_check['tables'] else 'No tables found'}")
    
    if 'Report' in db_check['tables']:
        print(f"\n=== Report Table Structure ===")
        for col in db_check['report_columns']:
            print(f"- {col['name']}: {col['type']} {'(PK)' if col['pk'] else ''}")
        
        print(f"\n=== Report Count ===")
        print(f"Total reports: {db_check['report_count']}")
        
        if db_check['sample_reports']:
            print("\n=== Sample Reports ===")
            for report in db_check['sample_reports']:
                print(f"- {report['reportId']}: {report['title']} ({report['status']}) - {report['createdAt']}")
    
    # Test report lookup
    test_id = "4d14ffa4138d4bd0"
    print(f"\n=== Testing Report Lookup: {test_id} ===")
    result = test_report_lookup(test_id)
    
    if result.get('success'):
        print(f"✅ Found report by {result['found_by']}:")
        print(json.dumps(result['report'], indent=2, default=str))
    else:
        print(f"❌ {result.get('error', 'Unknown error')}")
        if 'available_reports' in result and result['available_reports']:
            print("\nAvailable reports (first 10):")
            for r in result['available_reports']:
                print(f"- ID: {r.get('id')}, ReportID: {r.get('reportId')}, "
                      f"Title: {r.get('title')}, Status: {r.get('status')}")
