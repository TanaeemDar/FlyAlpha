"""Exchange client interfaces.

Adapters intentionally speak in simple REST-like records so crypto and forex
providers can be implemented without touching the fly-learning modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Ticker:
    symbol: str
    bid: float
    ask: float
    last: float


@dataclass(frozen=True)
class Balance:
    asset: str
    free: float
    total: float


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    quantity: float
    order_type: str = "market"


@dataclass(frozen=True)
class Order:
    order_id: str
    symbol: str
    side: str
    quantity: float
    status: str
    fill_price: float | None = None


class ExchangeClient(Protocol):
    """Minimum client contract required by FlyAlpha live loops."""

    def get_ticker(self, symbol: str) -> Ticker:
        """Fetch the current ticker."""

    def get_balance(self, asset: str) -> Balance:
        """Fetch account balance for one asset."""

    def place_order(self, request: OrderRequest) -> Order:
        """Place an order or record a paper order."""

