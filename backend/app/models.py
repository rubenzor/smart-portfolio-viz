# backend/app/models.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from .db import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, default="mixed")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Stored as JSON string
    benchmarks = Column(Text, default="[]")

    # Relationship with assets
    assets = relationship(
        "Asset", back_populates="portfolio", cascade="all, delete-orphan"
    )

    # -------------------------
    # Properties
    # -------------------------

    @property
    def benchmarks_list(self):
        """Return benchmarks as python list."""
        try:
            return json.loads(self.benchmarks)
        except:
            return []

    @benchmarks_list.setter
    def benchmarks_list(self, value):
        if not isinstance(value, list):
            raise ValueError("benchmarks must be a list")
        self.benchmarks = json.dumps(value)

    @property
    def benchmarks_py(self):
        """Alias used by Pydantic serializer."""
        return self.benchmarks_list


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    weight = Column(Float, default=0.0)
    benchmark = Column(String, nullable=False)

    portfolio = relationship("Portfolio", back_populates="assets")
