from typing import Optional
from auth.password_utils import hash_password, verify_password
from auth.session_manager import create_session
from data.repositories.users_repo import UsersRepo

class AuthService:
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
        repo.close()
        return create_session(user_id=user_id, ip=ip)
