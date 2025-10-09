from __future__ import annotations
from typing import Optional, Dict, Any
from data.duckdb_connector import DuckDBConnection

# Definición de tablas
DDL_USERS = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  name TEXT,
  role TEXT DEFAULT 'user',
  date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  user_id INTEGER REFERENCES users(user_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,
  active_flag BOOLEAN DEFAULT TRUE
);
"""

DDL_AUTH_LOG = """
CREATE TABLE IF NOT EXISTS users_auth_log (
  log_id BIGINT PRIMARY KEY,
  user_id INTEGER,
  login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip_address TEXT,
  token_preview TEXT,
  status TEXT
);
"""

class UsersRepo:
    """Repositorio para manejar usuarios y sesiones (una sola base)."""

    def __init__(self):
        self.db = DuckDBConnection(read_only=False)
        self.db.execute(DDL_USERS)
        self.db.execute(DDL_SESSIONS)
        self.db.execute(DDL_AUTH_LOG)

    # ────────────────────────────────────────────────────────────────
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM users WHERE email = ?;", (email,))
        return None if df.empty else df.iloc[0].to_dict()

    def create_user(self, email: str, hashed_password: str, name: str, role: str="user") -> int:
        next_id = self.db.df("SELECT COALESCE(MAX(user_id),0)+1 AS nid FROM users;").iloc[0]["nid"]
        self.db.execute(
            "INSERT INTO users(user_id,email,hashed_password,name,role) VALUES (?,?,?,?,?);",
            (int(next_id), email, hashed_password, name, role)
        )
        return int(next_id)

    def insert_session(self, session_id: str, user_id: int, expires_at: str):
        self.db.execute(
            "INSERT INTO sessions(session_id,user_id,expires_at) VALUES (?,?,?);",
            (session_id, user_id, expires_at)
        )

    def deactivate_session(self, session_id: str):
        self.db.execute("UPDATE sessions SET active_flag=FALSE WHERE session_id=?;", (session_id,))

    def log_auth(self, user_id: Optional[int], ip: str, token_preview: str, status: str):
        next_id = self.db.df("SELECT COALESCE(MAX(log_id),0)+1 AS nid FROM users_auth_log;").iloc[0]["nid"]
        self.db.execute(
            "INSERT INTO users_auth_log(log_id,user_id,ip_address,token_preview,status) VALUES (?,?,?,?,?);",
            (int(next_id), user_id if user_id else None, ip, token_preview[:12], status)
        )

    def close(self):
        self.db.close()
