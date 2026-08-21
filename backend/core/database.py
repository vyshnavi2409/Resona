import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def create_user(fullname: str, email: str, password_hash: str) -> str:
    user_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (id, fullname, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, fullname, email, password_hash, created_at)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already exists")
    conn.close()
    return user_id

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, fullname, email, password_hash FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "fullname": row[1], "email": row[2], "password_hash": row[3]}
    return None

def get_user_by_id(user_id: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, fullname, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "fullname": row[1], "email": row[2]}
    return None

def create_session(user_id: str, title: str = "New Chat") -> str:
    session_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, user_id, created_at, title) VALUES (?, ?, ?, ?)",
        (session_id, user_id, created_at, title)
    )
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions(user_id: str) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, title FROM sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [{"id": r[0], "created_at": r[1], "title": r[2]} for r in rows]

def get_session_messages(session_id: str, user_id: str) -> List[Dict]:
    # First verify ownership
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row or row[0] != user_id:
        conn.close()
        raise PermissionError("Access denied")

    cursor.execute(
        "SELECT id, role, content, sources, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for r in rows:
        messages.append({
            "id": r[0],
            "role": r[1],
            "content": r[2],
            "sources": json.loads(r[3]) if r[3] else [],
            "created_at": r[4]
        })
    return messages

def add_message(session_id: str, user_id: str, role: str, content: str, sources: Optional[List[str]] = None) -> str:
    # First verify ownership
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row or row[0] != user_id:
        conn.close()
        raise PermissionError("Access denied")

    msg_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    sources_json = json.dumps(sources) if sources else None
    
    cursor.execute(
        "INSERT INTO messages (id, session_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, session_id, role, content, sources_json, created_at)
    )
    
    # Optionally update session title based on first message
    if role == "user":
        cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
        if cursor.fetchone()[0] == 1:
            title = content[:30] + "..." if len(content) > 30 else content
            cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
            
    conn.commit()
    conn.close()
    return msg_id

# Initialize database on import
init_db()
