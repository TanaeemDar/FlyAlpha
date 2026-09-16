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


def execute_position(action: TradingAction, entry: MarketCandle, exit_: MarketCandle, cost_bps: float = 1.0) -> ExecutionResult:
    notional_change = exit_.close - entry.close
    if action is TradingAction.LONG:
        pnl = notional_change
        cost_multiplier = 1.0
    elif action is TradingAction.SHORT:
        pnl = -notional_change
        cost_multiplier = 1.0
    else:
        pnl = 0.0
        cost_multiplier = 0.0
    transaction_cost = entry.close * (cost_bps / 10_000.0) * cost_multiplier
    return ExecutionResult(action=action, pnl=pnl, transaction_cost=transaction_cost)

