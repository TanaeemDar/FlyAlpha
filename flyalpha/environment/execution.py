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
    breakeven_trigger_pct: float | None = None,
    trailing_stop_pct: float | None = None,
) -> ExecutionResult:
    exit_price = exit_.close
    exit_reason = "close"

    if action is TradingAction.LONG:
        adjusted_stop = _long_adjusted_stop(entry.close, exit_.high, stop_price, breakeven_trigger_pct, trailing_stop_pct)
        if adjusted_stop is not None and exit_.low <= adjusted_stop:
            exit_price = adjusted_stop
            exit_reason = "stop"
        elif take_profit_price is not None and exit_.high >= take_profit_price:
            exit_price = take_profit_price
            exit_reason = "take_profit"
    elif action is TradingAction.SHORT:
        adjusted_stop = _short_adjusted_stop(entry.close, exit_.low, stop_price, breakeven_trigger_pct, trailing_stop_pct)
        if adjusted_stop is not None and exit_.high >= adjusted_stop:
            exit_price = adjusted_stop
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


def _long_adjusted_stop(
    entry_price: float,
    high: float,
    stop_price: float | None,
    breakeven_trigger_pct: float | None,
    trailing_stop_pct: float | None,
) -> float | None:
    adjusted = stop_price
    if breakeven_trigger_pct and high >= entry_price * (1.0 + breakeven_trigger_pct):
        adjusted = max(adjusted or entry_price, entry_price)
    if trailing_stop_pct:
        trail = high * (1.0 - trailing_stop_pct)
        adjusted = max(adjusted or trail, trail)
    return adjusted


def _short_adjusted_stop(
    entry_price: float,
    low: float,
    stop_price: float | None,
    breakeven_trigger_pct: float | None,
    trailing_stop_pct: float | None,
) -> float | None:
    adjusted = stop_price
    if breakeven_trigger_pct and low <= entry_price * (1.0 - breakeven_trigger_pct):
        adjusted = min(adjusted or entry_price, entry_price)
    if trailing_stop_pct:
        trail = low * (1.0 + trailing_stop_pct)
        adjusted = min(adjusted or trail, trail)
    return adjusted
