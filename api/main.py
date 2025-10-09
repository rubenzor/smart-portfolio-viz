from fastapi import FastAPI
from api.routers import auth, portfolio

app = FastAPI(title="Smart Portfolio Viz API", version="v1")
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(portfolio.router, tags=["Portfolios"])