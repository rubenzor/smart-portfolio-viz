import os, time, hmac, base64, json
from hashlib import sha256

SECRET = os.getenv("APP_SECRET", "dev-secret-change-me")
TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "86400"))  # 1 día

def sign(payload: dict, ttl: int = TTL_SECONDS) -> str:
    data = payload.copy()
    data["exp"] = int(time.time()) + ttl
    raw = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(SECRET.encode(), raw, sha256).digest()
    return base64.urlsafe_b64encode(raw).decode() + "." + base64.urlsafe_b64encode(sig).decode()

def verify(token: str) -> dict | None:
    try:
        raw_b64, sig_b64 = token.split(".")
        raw = base64.urlsafe_b64decode(raw_b64.encode())
        sig = base64.urlsafe_b64decode(sig_b64.encode())
        exp_sig = hmac.new(SECRET.encode(), raw, sha256).digest()
        if not hmac.compare_digest(sig, exp_sig):
            return None
        data = json.loads(raw.decode())
        if data.get("exp", 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None
