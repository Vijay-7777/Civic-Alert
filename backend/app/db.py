import sqlite3
import os
import logging
from typing import Optional, Dict, Any, List, Iterator, Union
from pathlib import Path
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database path from config
from .config import DATABASE_PATH, BASE_DIR

# Resolve database path from known candidates to use the real dataset
def resolve_database_path() -> str:
    candidates = [
        BASE_DIR / "frontend" / "data" / "crime_lens.db",
        BASE_DIR / "backend" / "frontend" / "data" / "crime_lens.db",
        BASE_DIR / "data" / "crime_lens.db",
        Path(__file__).resolve().parent.parent / "data" / "crime_lens.db",
        Path(DATABASE_PATH),
    ]
    for p in candidates:
        try:
            path_obj = Path(p).resolve()
            if path_obj.exists():
                return str(path_obj)
        except Exception:
            continue
    # Fallback to configured path
    return str(Path(DATABASE_PATH).resolve())

def ensure_database_exists(db_path_str: str) -> bool:
    """Ensure the database directory exists. Do NOT auto-create a new empty DB that hides real data."""
    try:
        db_path = Path(db_path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        if not db_path.exists():
            logger.warning(f"Database file not found at {db_path}. Will not auto-create to avoid masking real data.")
            return False
        return True
    except Exception as e:
        logger.error(f"Error ensuring database exists: {e}")
        return False

@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    """Get a database connection with row factory and error handling"""
    db_path_str = resolve_database_path()
    logger.info(f"Connecting to database at: {db_path_str}")
    exists = ensure_database_exists(db_path_str)
    if not exists:
        logger.error(f"Database file not found: {db_path_str}")
        raise FileNotFoundError(f"Database file not found: {db_path_str}")
    conn = None
    try:
        conn = sqlite3.connect(db_path_str, timeout=30.0)  # 30 second timeout
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')  # Enable Write-Ahead Logging
        conn.execute('PRAGMA foreign_keys=ON')   # Enable foreign key constraints
        initialize_schema(conn)
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_db_connection: {e}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")

def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create required tables if they do not exist (safe idempotent)."""
    try:
        cursor = conn.cursor()
        # Create Report table (aligned with frontend schema)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Report (
              id TEXT PRIMARY KEY,
              reportId TEXT NOT NULL UNIQUE,
              type TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT NOT NULL,
              specificType TEXT NOT NULL,
              location TEXT,
              latitude REAL,
              longitude REAL,
              image TEXT,
              status TEXT NOT NULL DEFAULT 'PENDING',
              isAnonymous INTEGER NOT NULL DEFAULT 1,
              reporterName TEXT,
              reporterEmail TEXT,
              reporterPhone TEXT,
              reporterUserId INTEGER,
              departmentId INTEGER,
              departmentName TEXT,
              createdAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
              updatedAt TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_status ON Report(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_reportId ON Report(reportId)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_created_at ON Report(createdAt)")
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error initializing schema: {e}")

def dict_from_row(row: sqlite3.Row) -> Optional[Dict[str, Any]]:
    """Convert sqlite3.Row to dictionary"""
    if row is None:
        return None
    try:
        return dict(row)
    except Exception as e:
        logger.error(f"Error converting row to dict: {e}")
        return None

def fetch_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a specific report by ID (supports both numeric and UUID reportId)"""
    logger = logging.getLogger(__name__)
    
    if not report_id:
        logger.warning("fetch_report called with empty report_id")
        return None
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First try with the exact reportId
            query = """
            SELECT id, reportId, type, title, description, specificType, 
                   location, latitude, longitude, status, isAnonymous,
                   reporterName, reporterEmail, reporterPhone, reporterUserId,
                   departmentId, departmentName, 
                   strftime('%Y-%m-%d %H:%M:%S', createdAt) as createdAt,
                   strftime('%Y-%m-%d %H:%M:%S', updatedAt) as updatedAt
            FROM Report
            WHERE reportId = ? COLLATE NOCASE
            """
            logger.debug(f"Executing report query with reportId: {report_id}")
            cursor.execute(query, (report_id,))
            row = cursor.fetchone()
            
            # If not found, try with numeric ID as fallback
            if not row and report_id.isdigit():
                logger.debug(f"Trying with numeric ID: {report_id}")
                query = """
                SELECT id, reportId, type, title, description, specificType, 
                       location, latitude, longitude, status, isAnonymous,
                       reporterName, reporterEmail, reporterPhone, reporterUserId,
                       departmentId, departmentName,
                       strftime('%Y-%m-%d %H:%M:%S', createdAt) as createdAt,
                       strftime('%Y-%m-%d %H:%M:%S', updatedAt) as updatedAt
                FROM Report
                WHERE id = ?
                """
                cursor.execute(query, (int(report_id),))
                row = cursor.fetchone()
            
            if row:
                # Convert to dict and ensure all fields are present
                report = dict(row)
                # Ensure status is always a string and lowercase
                report['status'] = str(report.get('status', 'pending')).lower()
                logger.debug(f"Found report: {report.get('reportId', 'unknown')}")
                return report
                
            logger.warning(f"No report found with ID: {report_id}")
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Database error in fetch_report: {e}")
        logger.error(f"SQLite error: {e.sqlite_error_name if hasattr(e, 'sqlite_error_name') else 'N/A'}")
        logger.error(f"Error code: {e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in fetch_report: {e}", exc_info=True)
        return None

def create_report(report_data: Dict[str, Any]) -> str:
    """Create a new report using frontend schema"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        INSERT INTO Report (
            reportId, type, title, description, specificType, location,
            latitude, longitude, status, isAnonymous, reporterName,
            reporterEmail, reporterPhone, reporterUserId, departmentId,
            departmentName, image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            report_data.get("reportId"),
            report_data.get("type"),
            report_data.get("title"),
            report_data.get("description"),
            report_data.get("specificType"),
            report_data.get("location"),
            report_data.get("latitude"),
            report_data.get("longitude"),
            report_data.get("status", "PENDING"),
            1 if report_data.get("isAnonymous", True) else 0,
            report_data.get("reporterName"),
            report_data.get("reporterEmail"),
            report_data.get("reporterPhone"),
            report_data.get("reporterId"),
            report_data.get("departmentId"),
            report_data.get("departmentName"),
            report_data.get("image")
        ))
        
        conn.commit()
        return report_data.get("reportId")

def update_report_status(report_id: str, status: str) -> bool:
    """Update report status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
        UPDATE Report
        SET status = ?, updatedAt = datetime('now', 'localtime')
        WHERE reportId = ?
        """
        cursor.execute(query, (status, report_id))
        conn.commit()
        return cursor.rowcount > 0

def list_reports(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """List reports with optional filters"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        base_query = """
        SELECT id, reportId, type, title, description, specificType,
               location, latitude, longitude, status, isAnonymous,
               reporterName, reporterEmail, reporterPhone, reporterUserId,
               departmentId, departmentName, createdAt, updatedAt
        FROM Report
        """
        
        conditions = []
        params = []
        
        if filters:
            if "status" in filters:
                conditions.append("status = ?")
                params.append(filters["status"])
            
            if "type" in filters:
                conditions.append("type = ?")
                params.append(filters["type"])
            
            if "reporterUserId" in filters:
                conditions.append("reporterUserId = ?")
                params.append(filters["reporterUserId"])
            
            if "reporterEmail" in filters:
                conditions.append("reporterEmail = ?")
                params.append(filters["reporterEmail"])
            
            if "departmentName" in filters:
                conditions.append("departmentName = ?")
                params.append(filters["departmentName"])
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY createdAt DESC"
        
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
        SELECT id, email, name, role, departmentId, createdAt, updatedAt
        FROM User
        WHERE email = ?
        """
        cursor.execute(query, (email,))
        row = cursor.fetchone()
        return dict_from_row(row)

def get_departments() -> List[Dict[str, Any]]:
    """Get all departments"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
        SELECT id, name, description, createdAt, updatedAt
        FROM Department
        ORDER BY name
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]
