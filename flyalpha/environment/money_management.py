"""Money-management rules for simulated FlyAlpha trades."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.actions import TradingAction
from flyalpha.senses import MarketCandle


@dataclass(frozen=True)
class MoneyManagementConfig:
    """Risk controls used by the offline simulator."""

    initial_equity: float = 10_000.0
    risk_per_trade: float = 0.01
    stop_loss_pct: float = 0.01
    take_profit_pct: float | None = 0.02
    max_position_fraction: float = 1.0
    max_leverage: float = 1.0
    cost_bps: float = 1.0
    min_quantity: float = 0.0


@dataclass(frozen=True)
class PositionPlan:
    """Sized position and protective levels for one candle transition."""

    action: TradingAction
    quantity: float
    stop_price: float | None
    take_profit_price: float | None
    notional: float


def plan_position(
    action: TradingAction,
    entry: MarketCandle,
    equity: float,
    config: MoneyManagementConfig,
) -> PositionPlan:
    """Size a position from account equity and per-trade risk."""

    if action is TradingAction.FLAT or equity <= 0.0:
        return PositionPlan(action=TradingAction.FLAT, quantity=0.0, stop_price=None, take_profit_price=None, notional=0.0)

    stop_distance = entry.close * config.stop_loss_pct
    if stop_distance <= 0.0:
        return PositionPlan(action=TradingAction.FLAT, quantity=0.0, stop_price=None, take_profit_price=None, notional=0.0)

    risk_budget = equity * config.risk_per_trade
    risk_quantity = risk_budget / stop_distance
    max_notional = equity * config.max_position_fraction * config.max_leverage
    capped_quantity = max_notional / entry.close if entry.close > 0.0 else 0.0
    quantity = max(0.0, min(risk_quantity, capped_quantity))

    if quantity < config.min_quantity:
        return PositionPlan(action=TradingAction.FLAT, quantity=0.0, stop_price=None, take_profit_price=None, notional=0.0)

    if action is TradingAction.LONG:
        stop_price = entry.close * (1.0 - config.stop_loss_pct)
        take_profit_price = entry.close * (1.0 + config.take_profit_pct) if config.take_profit_pct else None
    else:
        stop_price = entry.close * (1.0 + config.stop_loss_pct)
        take_profit_price = entry.close * (1.0 - config.take_profit_pct) if config.take_profit_pct else None

    return PositionPlan(
        action=action,
        quantity=quantity,
        stop_price=stop_price,
        take_profit_price=take_profit_price,
        notional=quantity * entry.close,
    )

