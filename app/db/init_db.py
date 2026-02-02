"""
Database initialization for Job Application Tracker.
Creates SQLite tables for applications, events, emails_processed, and system_state.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import DB_PATH


def create_tables(db_path=None):
    """Create all required database tables."""
    if db_path is None:
        db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role_title TEXT NOT NULL,
            platform TEXT,
            source TEXT,
            applied_date DATETIME,
            first_seen_date DATETIME NOT NULL,
            status TEXT NOT NULL DEFAULT 'applied',
            last_updated DATETIME NOT NULL,
            portal_link TEXT,
            notes TEXT,
            UNIQUE(company, role_title, applied_date)
        )
    """)
    
    # Events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_time DATETIME NOT NULL,
            email_message_id TEXT NOT NULL,
            subject TEXT,
            from_email TEXT,
            confidence REAL,
            extracted_json TEXT,
            action_suggestion TEXT,
            FOREIGN KEY (application_id) REFERENCES applications(application_id),
            UNIQUE(email_message_id, application_id)
        )
    """)
    
    # Emails processed table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails_processed (
            email_message_id TEXT PRIMARY KEY,
            thread_id TEXT,
            received_at DATETIME NOT NULL,
            from_domain TEXT,
            subject TEXT,
            classification TEXT,
            processed_at DATETIME NOT NULL
        )
    """)
    
    # System state table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Initialize system state with default values
    cursor.execute("""
        INSERT OR IGNORE INTO system_state (key, value)
        VALUES ('last_checked_iso', ?)
    """, (datetime.utcnow().isoformat(),))
    
    # Create indexes for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_applications_status 
        ON applications(status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_applications_last_updated 
        ON applications(last_updated DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_application_id 
        ON events(application_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_event_time 
        ON events(event_time DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_emails_processed_received_at 
        ON emails_processed(received_at DESC)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database initialized at {db_path}")


def reset_database(db_path=None):
    """Drop all tables and recreate them. USE WITH CAUTION."""
    if db_path is None:
        db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop all tables
    cursor.execute("DROP TABLE IF EXISTS events")
    cursor.execute("DROP TABLE IF EXISTS applications")
    cursor.execute("DROP TABLE IF EXISTS emails_processed")
    cursor.execute("DROP TABLE IF EXISTS system_state")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database reset at {db_path}")
    
    # Recreate tables
    create_tables(db_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Job Application Tracker database")
    parser.add_argument("--reset", action="store_true", help="Reset database (DELETE ALL DATA)")
    parser.add_argument("--db-path", help="Custom database path")
    
    args = parser.parse_args()
    
    db_path = args.db_path or DB_PATH
    
    if args.reset:
        confirm = input(f"⚠️  WARNING: This will DELETE ALL DATA in {db_path}. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            reset_database(db_path)
        else:
            print("Reset cancelled")
    else:
        create_tables(db_path)
