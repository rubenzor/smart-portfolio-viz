from typing import Optional
from datetime import datetime,timedelta,timezone
import secrets

from auth.password_utils import hash_password, verify_password
from auth.session_manager import create_session
from data.repositories.users_repo import UsersRepo

TOKEN_DURATION_SECONDS = 15 *60 # Duración de los tokens de recuperación


class AuthService:
    # ────────────────────────────────────────────────
    # REGISTRO Y LOGIN
    # ────────────────────────────────────────────────
    @staticmethod
    def register(name: str, email: str, password: str) -> int:
        repo = UsersRepo()
        if repo.get_by_email(email):
            repo.close()
            raise ValueError("Email already registered")

        user_id = repo.create_user(email=email, hashed_password=hash_password(password), name=name)
        repo.close()
        return user_id

    @staticmethod
    def login(email: str, password: str, ip: str = "-") -> str:
        repo = UsersRepo()
        row = repo.get_by_email(email)
        if not row or not verify_password(password, row["hashed_password"]):
            repo.log_auth(None, ip, token_preview="invalid", status="LOGIN_FAIL")
            repo.close()
            raise ValueError("Invalid credentials")

        user_id = int(row["user_id"])
        repo.log_auth(user_id, ip, token_preview="ok", status="LOGIN_SUCCESS")
        repo.close()
        return create_session(user_id=user_id, ip=ip)

    # ────────────────────────────────────────────────
    # UTILIDADES DE USUARIO
    # ────────────────────────────────────────────────
    @staticmethod
    def user_exists(email: str) -> bool:
        repo = UsersRepo()
        user = repo.get_by_email(email)
        repo.close()
        return bool(user)

    @staticmethod
    def get_user_hashed_password(email: str) -> Optional[str]:
        repo = UsersRepo()
        row = repo.get_by_email(email)
        repo.close()
        return row["hashed_password"] if row else None

    @staticmethod
    def update_password(email: str, new_password: str):
        repo = UsersRepo()
        user = repo.get_by_email(email)
        if not user:
            repo.close()
            raise ValueError("User not found")

        new_hash = hash_password(new_password)
        repo.update_password(user["user_id"], new_hash)
        repo.close()

    # ────────────────────────────────────────────────
    # TOKEN DE RESET (PERSISTENTE EN BASE DE DATOS)
    # ────────────────────────────────────────────────
    @staticmethod
    def generate_reset_token(email: str) -> str:
        """Genera un token y lo guarda en la BD (válido por 15 minutos)."""
        repo = UsersRepo()
        user = repo.get_by_email(email)
        if not user:
            repo.close()
            raise ValueError("User not found")

        token = secrets.token_urlsafe(20)
        # 🔹 Fuerza a usar UTC real y consistente con la BD
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_DURATION_SECONDS)
        created_at = datetime.now(timezone.utc)

        next_id = repo.db.df(
            "SELECT COALESCE(MAX(token_id), 0) + 1 AS nid FROM password_reset_tokens;"
        ).iloc[0]["nid"]

        repo.db.execute(
        """
        INSERT INTO password_reset_tokens(token_id, user_id, token, expires_at, used, created_at)
        VALUES (?, ?, ?, ?, FALSE, ?);
        """,
        (int(next_id), user["user_id"], token, expires_at, created_at),
        )

        repo.close()
        return token


    @staticmethod
    def verify_reset_token(token: str) -> Optional[str]:
        """Busca el token en la BD y valida su vigencia."""
        repo = UsersRepo()
        df = repo.db.df("""
            SELECT prt.token, prt.expires_at, prt.used, u.email
            FROM password_reset_tokens prt
            JOIN users u ON prt.user_id = u.user_id
            WHERE prt.token = ?;
        """, (token,))
        repo.close()

        if df.empty:
            return None

        row = df.iloc[0]
        expires_at = row["expires_at"]
        used = row["used"]

        # ⚙️ Normalizar expires_at a datetime con zona horaria UTC
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        elif expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # 🔐 Verificar expiración y uso
        now = datetime.now(timezone.utc)
        if used or now > expires_at:
            return None

        return row["email"]


    @staticmethod
    def consume_reset_token(email: str):
        """Marca el token del usuario como usado tras restablecer la contraseña."""
        repo = UsersRepo()
        repo.db.execute("""
            UPDATE password_reset_tokens
            SET used = TRUE
            WHERE user_id = (SELECT user_id FROM users WHERE email = ?)
            AND used = FALSE;
        """, (email,))
        repo.close()
        # ────────────────────────────────────────────────
        # VERIFICACIÓN INTERNA DE CONTRASEÑAS
        # ────────────────────────────────────────────────
    @staticmethod
    def _verify_password_internal(password: str, hashed_password: str) -> bool:
        return verify_password(password, hashed_password)
