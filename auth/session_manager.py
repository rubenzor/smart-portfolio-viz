from datetime import datetime, timedelta
from auth.tokens import sign, verify
from data.repositories.users_repo import UsersRepo

def create_session(user_id: int, ip: str | None = None) -> str:
    token = sign({"user_id": user_id})
    expires_at = (datetime.now() + timedelta(days=1)).isoformat()
    repo = UsersRepo()
    repo.insert_session(session_id=token, user_id=user_id, expires_at=expires_at)
    repo.log_auth(user_id, ip or "-", token_preview=token, status="LOGIN_OK")
    repo.close()
    return token

def invalidate_session(token: str):
    repo = UsersRepo()
    repo.deactivate_session(token)
    repo.log_auth(None, "-", token_preview=token, status="LOGOUT")
    repo.close()

def get_session_user(token: str) -> int | None:
    data = verify(token)
    return data.get("user_id") if data else None
