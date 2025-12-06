# backend/app/routers/portfolios.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])

MAX_BENCHMARKS = 4
MAX_ASSETS_PER_BENCH = 5


# -----------------------------------
# Helpers
# -----------------------------------

def validate_benchmarks(benchmarks: List[str]):
    if len(benchmarks) > MAX_BENCHMARKS:
        raise HTTPException(400, f"Max {MAX_BENCHMARKS} benchmarks allowed")


def validate_assets_benchmarks(assets: List[schemas.AssetCreate]):
    bench_count = {}

    for a in assets:
        b = a.benchmark
        bench_count[b] = bench_count.get(b, 0) + 1

    for b, count in bench_count.items():
        if count > MAX_ASSETS_PER_BENCH:
            raise HTTPException(
                400,
                f"Benchmark '{b}' exceeds {MAX_ASSETS_PER_BENCH} assets (found {count})"
            )


# -----------------------------------
# Create portfolio
# -----------------------------------

@router.post("", response_model=schemas.PortfolioOut)
def create_portfolio(payload: schemas.PortfolioCreate, db: Session = Depends(get_db)):
    validate_benchmarks(payload.benchmarks)
    validate_assets_benchmarks(payload.assets)

    pf = models.Portfolio(
        name=payload.name,
        kind=payload.kind,
    )
    pf.benchmarks_list = payload.benchmarks   # <- Proper JSON list setter

    db.add(pf)
    db.flush()

    # Create assets
    for a in payload.assets:
        db.add(
            models.Asset(
                portfolio_id=pf.id,
                symbol=a.symbol.upper(),
                name=a.name,
                weight=a.weight,
                benchmark=a.benchmark,
            )
        )

    db.commit()
    db.refresh(pf)   # <- Now Pydantic will read pf.benchmarks_py
    return pf


# -----------------------------------
# List portfolios
# -----------------------------------

@router.get("", response_model=List[schemas.PortfolioOut])
def list_portfolios(db: Session = Depends(get_db)):
    portfolios = db.query(models.Portfolio).all()
    return portfolios     # <- DO NOT mutate benchmarks


# -----------------------------------
# Get portfolio
# -----------------------------------

@router.get("/{pf_id}", response_model=schemas.PortfolioOut)
def get_portfolio(pf_id: int, db: Session = Depends(get_db)):
    pf = db.query(models.Portfolio).filter_by(id=pf_id).first()
    if not pf:
        raise HTTPException(404, "Portfolio not found")
    return pf             # <- Let Pydantic use benchmarks_py


# -----------------------------------
# Update portfolio
# -----------------------------------

@router.put("/{pf_id}", response_model=schemas.PortfolioOut)
def update_portfolio(pf_id: int, payload: schemas.PortfolioUpdate, db: Session = Depends(get_db)):
    pf = db.query(models.Portfolio).filter_by(id=pf_id).first()
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    if payload.name:
        pf.name = payload.name

    if payload.kind:
        pf.kind = payload.kind

    # Update benchmarks list
    if payload.benchmarks is not None:
        validate_benchmarks(payload.benchmarks)
        pf.benchmarks_list = payload.benchmarks

    # Update assets
    if payload.assets is not None:
        validate_assets_benchmarks(payload.assets)

        # Remove previous assets
        db.query(models.Asset).filter_by(portfolio_id=pf_id).delete()

        for a in payload.assets:
            db.add(
                models.Asset(
                    portfolio_id=pf.id,
                    symbol=a.symbol.upper(),
                    name=a.name,
                    weight=a.weight,
                    benchmark=a.benchmark,
                )
            )

    db.commit()
    db.refresh(pf)
    return pf
