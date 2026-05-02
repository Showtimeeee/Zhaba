import sqlite3
import asyncio
from typing import Optional, List, Dict
from datetime import datetime


class Database:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, db_path: str = "data/zhaba.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "data/zhaba.db"):
        if self._initialized:
            return
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._initialized = True
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    sender TEXT,
                    ip TEXT,
                    message TEXT NOT NULL,
                    html BOOLEAN DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.commit()

    def add_message(self, subject: str, message: str, sender: str = None, ip: str = None, 
                   html: bool = False, status: str = 'pending') -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO messages (subject, message, sender, ip, html, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (subject, message, sender, ip, html, status))
            conn.commit()
            return cursor.lastrowid

    def update_message_status(self, message_id: int, status: str, error_message: str = None):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE messages
                SET status = ?, error_message = ?, sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, error_message, message_id))
            conn.commit()

    def get_message(self, message_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_messages(self, limit: int =100, offset: int = 0) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM messages
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM messages
            """)
            row = cursor.fetchone()
            return {
                'total': row[0] or 0,
                'sent': row[1] or 0,
                'failed': row[2] or 0,
                'pending': row[3] or 0
            }

    @classmethod
    def reset_instance(cls):
        """For testing purposes only"""
        cls._instance = None
