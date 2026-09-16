"""Deterministic mapping from MBON population dominance to market action."""

from __future__ import annotations

from enum import Enum


class TradingAction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


def action_from_population(population: str) -> TradingAction:
    mapping = {
        "approach": TradingAction.LONG,
        "avoidance": TradingAction.SHORT,
        "hold": TradingAction.FLAT,
    }
    try:
        return mapping[population]
    except KeyError as exc:
        raise ValueError(f"unknown output population: {population}") from exc

