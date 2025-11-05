from __future__ import annotations
from typing import Optional, Dict, Any
from data.duckdb_connector import DuckDBConnection
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# DDLs (definiciones de tablas)
# ────────────────────────────────────────────────
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
DDL_PASSWORD_RESET = """
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id INTEGER,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    token VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (token_id)
);
"""

class UsersRepo:
    """Repositorio para manejar usuarios, sesiones y recuperación de contraseñas."""

    def __init__(self):
        self.db = DuckDBConnection(read_only=False)
        self.db.execute(DDL_USERS)
        self.db.execute(DDL_SESSIONS)
        self.db.execute(DDL_AUTH_LOG)
        self.db.execute(DDL_PASSWORD_RESET)

    # ────────────────────────────────────────────────
    # USUARIOS
    # ────────────────────────────────────────────────
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM users WHERE email = ?;", (email,))
        return None if df.empty else df.iloc[0].to_dict()

    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM users WHERE user_id = ?;", (user_id,))
        return None if df.empty else df.iloc[0].to_dict()

    def create_user(self, email: str, hashed_password: str, name: str, role: str="user") -> int:
        next_id = self.db.df("SELECT COALESCE(MAX(user_id),0)+1 AS nid FROM users;").iloc[0]["nid"]
        self.db.execute(
            "INSERT INTO users(user_id,email,hashed_password,name,role) VALUES (?,?,?,?,?);",
            (int(next_id), email, hashed_password, name, role)
        )
        return int(next_id)

    def update_password(self, user_id: int, new_hashed_password: str):
        self.db.execute(
            "UPDATE users SET hashed_password = ? WHERE user_id = ?;",
            (new_hashed_password, user_id)
        )

    # ────────────────────────────────────────────────
    # TOKENS DE RESET
    # ────────────────────────────────────────────────
    def create_reset_token(self, user_id: int, token: str, minutes: int = 15):
        expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        next_id = self.db.df("SELECT COALESCE(MAX(token_id),0)+1 AS nid FROM password_reset_tokens;").iloc[0]["nid"]
        self.db.execute(
            "INSERT INTO password_reset_tokens(token_id,user_id,token,expires_at) VALUES (?,?,?,?);",
            (int(next_id), user_id, token, expires_at)
        )

    def get_user_by_token(self, token: str) -> Optional[int]:
        df = self.db.df(
            """
            SELECT user_id FROM password_reset_tokens
            WHERE token = ? AND used = FALSE AND expires_at > CURRENT_TIMESTAMP;
            """,
            (token,),
        )
        return None if df.empty else int(df.iloc[0]["user_id"])

    def mark_token_used(self, token: str):
        self.db.execute("UPDATE password_reset_tokens SET used = TRUE WHERE token = ?;", (token,))

    def clean_expired_tokens(self):
        self.db.execute("DELETE FROM password_reset_tokens WHERE expires_at < CURRENT_TIMESTAMP;")

    # ────────────────────────────────────────────────
    # SESIONES Y LOGS
    # ────────────────────────────────────────────────
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

