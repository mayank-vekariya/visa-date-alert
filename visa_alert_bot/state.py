from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

from .detector import normalize


class AlertState:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_messages (
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                processed_at INTEGER NOT NULL,
                PRIMARY KEY (chat_id, message_id)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_alerts (
                fingerprint TEXT PRIMARY KEY,
                sent_at INTEGER NOT NULL
            )
            """
        )
        self.connection.commit()

    @staticmethod
    def fingerprint(text: str) -> str:
        value = normalize(text)
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def mark_message_once(self, chat_id: int, message_id: int) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO processed_messages VALUES (?, ?, ?)",
            (chat_id, message_id, int(time.time())),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def mark_alert_if_fresh(self, text: str, window_seconds: int) -> bool:
        fingerprint = self.fingerprint(text)
        now = int(time.time())
        row = self.connection.execute(
            "SELECT sent_at FROM sent_alerts WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        if row and now - int(row[0]) < window_seconds:
            return False
        self.connection.execute(
            "INSERT INTO sent_alerts(fingerprint, sent_at) VALUES (?, ?) "
            "ON CONFLICT(fingerprint) DO UPDATE SET sent_at = excluded.sent_at",
            (fingerprint, now),
        )
        self.connection.commit()
        return True

    def prune(self, older_than_seconds: int = 604_800) -> None:
        cutoff = int(time.time()) - older_than_seconds
        self.connection.execute("DELETE FROM processed_messages WHERE processed_at < ?", (cutoff,))
        self.connection.execute("DELETE FROM sent_alerts WHERE sent_at < ?", (cutoff,))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
