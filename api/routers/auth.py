from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr
from auth.auth_service import AuthService
from auth.password_utils import verify_password
from auth.session_manager import get_session_user, invalidate_session
from typing import Optional
import re

router = APIRouter()

# ────────────────────────────────────────────────
# MODELOS
# ────────────────────────────────────────────────
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

# ────────────────────────────────────────────────
# ENDPOINTS DE AUTENTICACIÓN
# ────────────────────────────────────────────────
@router.post("/register")
def register(payload: RegisterIn):
    try:
        uid = AuthService.register(payload.name, payload.email, payload.password)
        return {"user_id": uid, "status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(payload: LoginIn, request: Request):
    try:
        ip = request.client.host if request.client else "-"
        token = AuthService.login(payload.email, payload.password, ip=ip)
        return {"access_token": token, "token_type": "Bearer"}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

@router.get("/me")
def me(authorization: Optional[str] = Depends(api_key_header)):
    """Devuelve el ID del usuario autenticado."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = authorization.split(" ", 1)[1] if authorization.startswith("Bearer ") else authorization.strip()
    user_id = get_session_user(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid/expired token")

    return {"user_id": user_id}

@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        invalidate_session(token)
    return {"status": "ok"}

# ────────────────────────────────────────────────
# OLVIDAR CONTRASEÑA
# ────────────────────────────────────────────────
@router.post("/forgot_password")
def forgot_password(payload: ForgotPasswordIn):
    email = payload.email

    if not AuthService.user_exists(email):
        raise HTTPException(status_code=404, detail="Email not registered")

    token = AuthService.generate_reset_token(email)
    print(f"🔐 Reset link for {email}: http://localhost:8000/?token={token}")

    return {"status": "ok", "message": "Reset link generated", "expires_in_minutes": 15}

# ────────────────────────────────────────────────
# VERIFICAR TOKEN
# ────────────────────────────────────────────────
@router.get("/verify_reset_token/{token}", summary="Verifica si un token de reset es válido y no ha expirado")
def verify_reset_token(token: str):
    email = AuthService.verify_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"email": email, "status": "valid"}

# ────────────────────────────────────────────────
# RESETEAR CONTRASEÑA
# ────────────────────────────────────────────────
@router.post("/reset_password")
def reset_password(payload: ResetPasswordIn):
    email = AuthService.verify_reset_token(payload.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Validar complejidad mínima
    if len(payload.new_password) < 8 or not re.search(r"[A-Z]", payload.new_password) or not re.search(r"[0-9]", payload.new_password):
        raise HTTPException(status_code=400, detail="Password must have at least 8 characters, 1 uppercase and 1 number")

    # Evitar que sea igual a la anterior
    old_hash = AuthService.get_user_hashed_password(email)
    if old_hash and verify_password(payload.new_password, old_hash):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old one")

    # Actualizar contraseña
    AuthService.update_password(email, payload.new_password)

    # Invalidar token
    AuthService.consume_reset_token(payload.token)

    return {"status": "ok", "message": "Password updated successfully"}

