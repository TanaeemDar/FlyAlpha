"""Reward functions for the fly environment."""

from __future__ import annotations

from .execution import ExecutionResult


def reward_from_execution(execution: ExecutionResult) -> float:
    return execution.pnl - execution.transaction_cost

