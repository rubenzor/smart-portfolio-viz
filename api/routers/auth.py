from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr
from auth.auth_service import AuthService
from auth.session_manager import get_session_user, invalidate_session
from typing import Optional
router = APIRouter()

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

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
@router.get(
    "/me",
    summary="Obtener el usuario autenticado",
    description="Devuelve el ID del usuario autenticado a partir del token devuelto por /auth/login.",
)
def me(authorization: Optional[str] = Depends(api_key_header)):
    """
    Puedes enviar el token en el header:
        Authorization: Bearer <token>
    """
    print("HEADER RECIBIDO:", authorization)

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth token")

    # Si viene con prefijo Bearer
    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization.strip()

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
