"""Minimal deterministic execution model."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.actions import TradingAction
from flyalpha.senses import MarketCandle


@dataclass(frozen=True)
class ExecutionResult:
    """Realized action outcome over one candle interval."""

    action: TradingAction
    pnl: float
    transaction_cost: float
    quantity: float = 1.0
    exit_price: float | None = None
    exit_reason: str = "close"


def execute_position(
    action: TradingAction,
    entry: MarketCandle,
    exit_: MarketCandle,
    cost_bps: float = 1.0,
    quantity: float = 1.0,
    stop_price: float | None = None,
    take_profit_price: float | None = None,
) -> ExecutionResult:
    exit_price = exit_.close
    exit_reason = "close"

    if action is TradingAction.LONG:
        if stop_price is not None and exit_.low <= stop_price:
            exit_price = stop_price
            exit_reason = "stop"
        elif take_profit_price is not None and exit_.high >= take_profit_price:
            exit_price = take_profit_price
            exit_reason = "take_profit"
    elif action is TradingAction.SHORT:
        if stop_price is not None and exit_.high >= stop_price:
            exit_price = stop_price
            exit_reason = "stop"
        elif take_profit_price is not None and exit_.low <= take_profit_price:
            exit_price = take_profit_price
            exit_reason = "take_profit"

    notional_change = exit_price - entry.close
    if action is TradingAction.LONG:
        pnl = notional_change * quantity
        cost_multiplier = 1.0
    elif action is TradingAction.SHORT:
        pnl = -notional_change * quantity
        cost_multiplier = 1.0
    else:
        pnl = 0.0
        cost_multiplier = 0.0
        quantity = 0.0
        exit_price = exit_.close
        exit_reason = "flat"
    transaction_cost = entry.close * quantity * (cost_bps / 10_000.0) * cost_multiplier
    return ExecutionResult(
        action=action,
        pnl=pnl,
        transaction_cost=transaction_cost,
        quantity=quantity,
        exit_price=exit_price,
        exit_reason=exit_reason,
    )
