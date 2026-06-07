import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from config import ATTENDANCE_DB_PATH, OTP_VALID_MINUTES

DB_PATH = Path(ATTENDANCE_DB_PATH)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    return sqlite3.connect(str(DB_PATH))

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS otp_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                email TEXT NOT NULL,
                otp_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY, 
                value INTEGER
            )
        """)
        cur.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('total_classes', 0)")
        conn.commit()

def record_attendance(student_id, name, email, confidence):
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO attendance (student_id, name, email, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, name, email, confidence, now))
        conn.commit()

def was_marked_recently(student_id, minutes=5):
    cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM attendance
            WHERE student_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (student_id, cutoff))
        return cur.fetchone() is not None

def get_student_attendance(student_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM attendance WHERE student_id = ?", (student_id,))
        row = cur.fetchone()
        return row[0]

def store_otp_session(student_id, email, otp_hash):
    now = datetime.now()
    expires_at = (now + timedelta(minutes=OTP_VALID_MINUTES)).isoformat(timespec="seconds")
    created_at = now.isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO otp_sessions (student_id, email, otp_hash, expires_at, verified, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (student_id, email, otp_hash, expires_at, created_at))
        conn.commit()

def verify_otp(student_id, otp_hash):
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, otp_hash, expires_at, verified
            FROM otp_sessions
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (student_id,))
        row = cur.fetchone()
        if row is None:
            return False
        session_id, stored_hash, expires_at, verified = row
        if verified == 1 or now > expires_at or stored_hash != otp_hash:
            return False
        cur.execute("UPDATE otp_sessions SET verified = 1 WHERE id = ?", (session_id,))
        conn.commit()
        return True
def increment_class_count():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE system_config SET value = value + 1 WHERE key = 'total_classes'")
        conn.commit()

def decrement_class_count():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE system_config SET value = MAX(0, value - 1) WHERE key = 'total_classes'")
        conn.commit()

def get_total_classes():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM system_config WHERE key = 'total_classes'")
        row = cur.fetchone()
        return row[0] if row else 0
def is_otp_verified(student_id):
    """Checks if the most recent OTP session for a student is marked as verified."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT verified
            FROM otp_sessions
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (student_id,))
        
        row = cur.fetchone()
        if row and row[0] == 1:
            return True
        return False
