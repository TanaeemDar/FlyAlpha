"""Deterministic market feature extraction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketCandle:
    """Single OHLCV candle."""

    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MarketFeatures:
    """Normalized sensory channels for the fly interface."""

    return_: float
    range_: float
    volume_change: float
    momentum: float
    volatility: float


def encode_market_features(previous: MarketCandle, current: MarketCandle) -> MarketFeatures:
    """Create deterministic features with no learned encoder."""

    prev_close = previous.close or 1.0
    prev_volume = previous.volume or 1.0
    return_ = (current.close - previous.close) / prev_close
    range_ = (current.high - current.low) / max(current.open, 1e-9)
    volume_change = (current.volume - previous.volume) / prev_volume
    momentum = (current.close - current.open) / max(current.open, 1e-9)
    volatility = abs(return_) + range_
    return MarketFeatures(
        return_=return_,
        range_=range_,
        volume_change=volume_change,
        momentum=momentum,
        volatility=volatility,
    )

