# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routers import portfolios, optimization, forecasting, overview, search, history    
from app.services.history_service import fetch_history


# Crea tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TFG Analytics Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para desarrollo con Dash
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolios.router)
app.include_router(optimization.router)
app.include_router(forecasting.router)
app.include_router(overview.router)
app.include_router(search.router, prefix="/api/v1")
app.include_router(history.router)

@app.get("/health")
def health():
    return {"ok": True}
