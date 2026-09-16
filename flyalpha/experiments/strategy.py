"""Deterministic trade filters around the fly-inspired decision layer."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.actions import TradingAction, action_from_population
from flyalpha.mushroom_body import MBONReadout
from flyalpha.senses import MarketCandle, encode_market_features


@dataclass(frozen=True)
class StrategyFilterConfig:
    """Non-neural gates used to suppress weak or noisy trades."""

    confidence_threshold: float = 0.0
    min_volatility: float = 0.0
    trend_lookback: int = 1
    require_trend_alignment: bool = False


def action_from_readout(
    readout: MBONReadout,
    previous: MarketCandle,
    current: MarketCandle,
    history: list[MarketCandle],
    config: StrategyFilterConfig | None = None,
) -> TradingAction:
    """Map MBON readout to action, then apply deterministic filters."""

    action = action_from_population(readout.dominant_population)
    config = config or StrategyFilterConfig()
    if action is TradingAction.FLAT:
        return action

    confidence = _confidence(readout)
    if confidence < config.confidence_threshold:
        return TradingAction.FLAT

    features = encode_market_features(previous, current)
    if features.volatility < config.min_volatility:
        return TradingAction.FLAT

    if config.require_trend_alignment and not _trend_allows(action, history, config.trend_lookback):
        return TradingAction.FLAT

    return action


def _confidence(readout: MBONReadout) -> float:
    directional = sorted((readout.approach, readout.avoidance), reverse=True)
    return directional[0] - directional[1]


def _trend_allows(action: TradingAction, history: list[MarketCandle], lookback: int) -> bool:
    if lookback <= 1 or len(history) < lookback:
        return True
    start = history[-lookback].close
    end = history[-1].close
    if action is TradingAction.LONG:
        return end >= start
    if action is TradingAction.SHORT:
        return end <= start
    return True
