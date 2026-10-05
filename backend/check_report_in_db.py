import sqlite3
from pathlib import Path

# Path to the database
db_path = Path(__file__).resolve().parents[1] / "frontend" / "data" / "crime_lens.db"

# Report ID to check
report_id = "4d14ffa4138d4bd0"

try:
    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    print(f"🔍 Checking for report with ID: {report_id}")
    print("-" * 60)
    
    # Query 1: Check in Report table by reportId
    cursor.execute("SELECT * FROM Report WHERE reportId = ?", (report_id,))
    report = cursor.fetchone()
    
    if report:
        print("✅ Report found in Report table:")
        print(dict(report))
    else:
        print("❌ Report not found in Report table with reportId:", report_id)
        
        # Query 2: Check in Report table by id
        cursor.execute("SELECT * FROM Report WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        
        if report:
            print("\n✅ Report found in Report table (matched by id):")
            print(dict(report))
        else:
            print("\n❌ Report not found in Report table with id:", report_id)
            
        # List all tables to help with debugging
        print("\n📋 Listing all tables in the database:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
            
            # For each table, check if it has a reportId or id column
            try:
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = [col[1] for col in cursor.fetchall()]
                if 'reportId' in columns or 'id' in columns:
                    print(f"  - Has columns: {', '.join(columns)}")
            except:
                pass
                
    # Show some sample reports if available
    print("\n📋 Sample reports (if any):")
    try:
        cursor.execute("SELECT id, reportId, title, status FROM Report LIMIT 5")
        samples = cursor.fetchall()
        if samples:
            for row in samples:
                print(f"- ID: {row['id']}, Report ID: {row['reportId']}, Title: {row['title']}, Status: {row['status']}")
        else:
            print("No reports found in the database")
    except Exception as e:
        print(f"Error fetching sample reports: {str(e)}")
        
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    
finally:
    if 'conn' in locals():
        conn.close()
