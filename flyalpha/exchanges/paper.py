"""Paper exchange adapter for safe local runs."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import Balance, Order, OrderRequest, Ticker


@dataclass
class PaperExchangeClient:
    """A deterministic exchange that records orders without network access."""

    starting_cash: float = 10_000.0
    last_price: float = 100.0
    orders: list[Order] = field(default_factory=list)

    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(symbol=symbol, bid=self.last_price - 0.01, ask=self.last_price + 0.01, last=self.last_price)

    def get_balance(self, asset: str) -> Balance:
        return Balance(asset=asset, free=self.starting_cash, total=self.starting_cash)

    def place_order(self, request: OrderRequest) -> Order:
        order = Order(
            order_id=f"paper-{len(self.orders) + 1}",
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            status="filled",
            fill_price=self.last_price,
        )
        self.orders.append(order)
        return order

