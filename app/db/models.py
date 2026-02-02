"""
Database models and query helpers for Job Application Tracker.
Provides clean interface for database operations.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

from app.config import DB_PATH


@contextmanager
def get_db_connection(db_path=None):
    """Context manager for database connections."""
    if db_path is None:
        db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()


# ===== System State =====

def get_system_state(key: str, default=None) -> Optional[str]:
    """Get a system state value."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_state WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def set_system_state(key: str, value: str):
    """Set a system state value."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO system_state (key, value)
            VALUES (?, ?)
        """, (key, value))
        conn.commit()


# ===== Emails Processed =====

def is_email_processed(message_id: str) -> bool:
    """Check if an email has already been processed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM emails_processed WHERE email_message_id = ?",
            (message_id,)
        )
        return cursor.fetchone() is not None


def mark_email_processed(
    message_id: str,
    thread_id: str,
    received_at: datetime,
    from_domain: str,
    subject: str,
    classification: str
):
    """Mark an email as processed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO emails_processed
            (email_message_id, thread_id, received_at, from_domain, subject, classification, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (message_id, thread_id, received_at, from_domain, subject, classification, datetime.utcnow()))
        conn.commit()


# ===== Applications =====

def create_application(
    company: str,
    role_title: str,
    platform: Optional[str] = None,
    source: Optional[str] = None,
    applied_date: Optional[datetime] = None,
    status: str = "applied",
    portal_link: Optional[str] = None,
    notes: Optional[str] = None
) -> int:
    """Create a new application record. Returns application_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow()
        
        cursor.execute("""
            INSERT INTO applications
            (company, role_title, platform, source, applied_date, first_seen_date, status, last_updated, portal_link, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (company, role_title, platform, source, applied_date, now, status, now, portal_link, notes))
        
        conn.commit()
        return cursor.lastrowid


def get_application_by_id(application_id: int) -> Optional[Dict]:
    """Get application by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM applications WHERE application_id = ?",
            (application_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def find_applications_by_company_role(company: str, role_title: str, threshold: int = 3) -> List[Dict]:
    """Find applications matching company and role (case-insensitive)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM applications
            WHERE LOWER(company) = LOWER(?)
            AND LOWER(role_title) = LOWER(?)
            ORDER BY last_updated DESC
        """, (company, role_title))
        
        return [dict(row) for row in cursor.fetchall()]


def find_applications_by_portal_link(portal_link: str) -> List[Dict]:
    """Find applications by portal link."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM applications
            WHERE portal_link = ?
            ORDER BY last_updated DESC
        """, (portal_link,))
        
        return [dict(row) for row in cursor.fetchall()]


def update_application_status(application_id: int, status: str, notes: Optional[str] = None):
    """Update application status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if notes:
            cursor.execute("""
                UPDATE applications
                SET status = ?, last_updated = ?, notes = ?
                WHERE application_id = ?
            """, (status, datetime.utcnow(), notes, application_id))
        else:
            cursor.execute("""
                UPDATE applications
                SET status = ?, last_updated = ?
                WHERE application_id = ?
            """, (status, datetime.utcnow(), application_id))
        
        conn.commit()


def get_all_applications(limit: Optional[int] = None) -> List[Dict]:
    """Get all applications, ordered by last_updated DESC."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM applications ORDER BY last_updated DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]


# ===== Events =====

def create_event(
    application_id: int,
    event_type: str,
    event_time: datetime,
    email_message_id: str,
    subject: str,
    from_email: str,
    confidence: float,
    extracted_json: Dict,
    action_suggestion: Optional[str] = None
) -> int:
    """Create a new event record. Returns event_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events
            (application_id, event_type, event_time, email_message_id, subject, from_email, confidence, extracted_json, action_suggestion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            application_id,
            event_type,
            event_time,
            email_message_id,
            subject,
            from_email,
            confidence,
            json.dumps(extracted_json),
            action_suggestion
        ))
        
        conn.commit()
        return cursor.lastrowid


def get_events_for_application(application_id: int) -> List[Dict]:
    """Get all events for an application."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM events
            WHERE application_id = ?
            ORDER BY event_time DESC
        """, (application_id,))
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['extracted_json'] = json.loads(event['extracted_json'])
            events.append(event)
        
        return events


def get_recent_events(limit: int = 100) -> List[Dict]:
    """Get recent events across all applications."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, a.company, a.role_title, a.status as application_status
            FROM events e
            JOIN applications a ON e.application_id = a.application_id
            ORDER BY e.event_time DESC
            LIMIT ?
        """, (limit,))
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['extracted_json'] = json.loads(event['extracted_json'])
            events.append(event)
        
        return events


# ===== Analytics Queries =====

def get_status_counts() -> Dict[str, int]:
    """Get count of applications by status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM applications
            GROUP BY status
            ORDER BY count DESC
        """)
        
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_applications_by_date_range(start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get applications within a date range."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM applications
            WHERE first_seen_date BETWEEN ? AND ?
            ORDER BY first_seen_date DESC
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]


def get_event_type_counts() -> Dict[str, int]:
    """Get count of events by type."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM events
            GROUP BY event_type
            ORDER BY count DESC
        """)
        
        return {row[0]: row[1] for row in cursor.fetchall()}
