from fastapi import FastAPI
from api.routers import auth as auth_router

app = FastAPI(title="Smart Portfolio Viz API", version="v1")
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
