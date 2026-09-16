"""Central trading loop entry points."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.actions import TradingAction
from flyalpha.exchanges import ExchangeClient, Order, OrderRequest, PaperExchangeClient, RestExchangeClient


@dataclass(frozen=True)
class TradingLoopResult:
    """Summary of one trading loop invocation."""

    mode: str
    symbol: str
    action: TradingAction
    order: Order | None
    last_price: float


def build_exchange(mode: str, base_url: str | None = None) -> ExchangeClient:
    if mode == "paper":
        return PaperExchangeClient()
    if mode == "live":
        if not base_url:
            raise ValueError("live mode requires --base-url for the exchange API")
        return RestExchangeClient(base_url=base_url)
    raise ValueError(f"unknown exchange mode: {mode}")


def run_trading_once(
    mode: str,
    symbol: str,
    action: TradingAction = TradingAction.FLAT,
    quantity: float = 0.0,
    base_url: str | None = None,
    live_confirmed: bool = False,
) -> TradingLoopResult:
    """Run one exchange-connected trading iteration.

    Paper mode records simulated orders. Live mode refuses to place orders
    unless the caller passes an explicit confirmation flag.
    """

    if action is not TradingAction.FLAT and quantity > 0.0:
        if mode == "live" and not live_confirmed:
            raise RuntimeError("live order blocked; pass --i-understand-live-risk to continue")

    exchange = build_exchange(mode=mode, base_url=base_url)
    ticker = exchange.get_ticker(symbol)
    order = None

    if action is not TradingAction.FLAT and quantity > 0.0:
        side = "buy" if action is TradingAction.LONG else "sell"
        order = exchange.place_order(OrderRequest(symbol=symbol, side=side, quantity=quantity))

    return TradingLoopResult(
        mode=mode,
        symbol=symbol,
        action=action,
        order=order,
        last_price=ticker.last,
    )
