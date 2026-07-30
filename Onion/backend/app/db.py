"""SQLite persistence layer. One DB file per instance, local-only."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS identity (
    id                INTEGER PRIMARY KEY CHECK (id = 1),
    public_key        TEXT NOT NULL,
    private_key       TEXT NOT NULL,
    onion_address     TEXT NOT NULL,
    onion_private_key TEXT,
    created_at        REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    alias         TEXT NOT NULL,
    onion_address TEXT NOT NULL UNIQUE,
    public_key    TEXT NOT NULL,
    created_at    REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_onion ON contacts(onion_address);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id      INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    direction       TEXT NOT NULL CHECK (direction IN ('sent','received')),
    content         TEXT NOT NULL,
    msg_uuid        TEXT NOT NULL UNIQUE,
    delivery_status TEXT NOT NULL DEFAULT 'sending'
                    CHECK (delivery_status IN ('sending','sent','delivered','failed')),
    created_at      REAL NOT NULL,
    remote_ts       REAL
);
CREATE INDEX IF NOT EXISTS idx_messages_contact_ts ON messages(contact_id, created_at);
"""


def get_connection(data_dir: str) -> sqlite3.Connection:
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    db_path = Path(data_dir) / "whisper.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# ---- identity ----

def get_identity(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM identity WHERE id = 1").fetchone()


def save_identity(
    conn: sqlite3.Connection,
    public_key: str,
    private_key: str,
    onion_address: str,
    onion_private_key: str | None,
    created_at: float,
) -> None:
    conn.execute(
        """
        INSERT INTO identity (id, public_key, private_key, onion_address, onion_private_key, created_at)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            public_key = excluded.public_key,
            private_key = excluded.private_key,
            onion_address = excluded.onion_address,
            onion_private_key = excluded.onion_private_key,
            created_at = excluded.created_at
        """,
        (public_key, private_key, onion_address, onion_private_key, created_at),
    )
    conn.commit()


def wipe_all(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM contacts")
    conn.execute("DELETE FROM identity")
    conn.commit()


# ---- contacts ----

def list_contacts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM contacts ORDER BY created_at").fetchall()


def get_contact(conn: sqlite3.Connection, contact_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()


def get_contact_by_onion(conn: sqlite3.Connection, onion_address: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM contacts WHERE onion_address = ?", (onion_address,)
    ).fetchone()


def create_contact(
    conn: sqlite3.Connection, alias: str, onion_address: str, public_key: str, created_at: float
) -> int:
    cur = conn.execute(
        "INSERT INTO contacts (alias, onion_address, public_key, created_at) VALUES (?, ?, ?, ?)",
        (alias, onion_address, public_key, created_at),
    )
    conn.commit()
    return cur.lastrowid


def delete_contact(conn: sqlite3.Connection, contact_id: int) -> None:
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()


# ---- messages ----

def list_messages(
    conn: sqlite3.Connection, contact_id: int, limit: int = 500, before_id: int | None = None
) -> list[sqlite3.Row]:
    if before_id is not None:
        rows = conn.execute(
            """
            SELECT * FROM messages
            WHERE contact_id = ? AND id < ?
            ORDER BY id DESC LIMIT ?
            """,
            (contact_id, before_id, limit),
        ).fetchall()
        return list(reversed(rows))
    rows = conn.execute(
        "SELECT * FROM messages WHERE contact_id = ? ORDER BY id DESC LIMIT ?",
        (contact_id, limit),
    ).fetchall()
    return list(reversed(rows))


def create_message(
    conn: sqlite3.Connection,
    contact_id: int,
    direction: str,
    content: str,
    msg_uuid: str,
    delivery_status: str,
    created_at: float,
    remote_ts: float | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO messages (contact_id, direction, content, msg_uuid, delivery_status, created_at, remote_ts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (contact_id, direction, content, msg_uuid, delivery_status, created_at, remote_ts),
    )
    conn.commit()
    return cur.lastrowid


def get_message_by_uuid(conn: sqlite3.Connection, msg_uuid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM messages WHERE msg_uuid = ?", (msg_uuid,)).fetchone()


def update_message_status(conn: sqlite3.Connection, msg_uuid: str, delivery_status: str) -> None:
    conn.execute(
        "UPDATE messages SET delivery_status = ? WHERE msg_uuid = ?", (delivery_status, msg_uuid)
    )
    conn.commit()


def delete_conversation(conn: sqlite3.Connection, contact_id: int) -> None:
    conn.execute("DELETE FROM messages WHERE contact_id = ?", (contact_id,))
    conn.commit()
