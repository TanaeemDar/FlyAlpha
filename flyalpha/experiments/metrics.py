"""Trading metrics for FlyAlpha experiment results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RewardMetrics:
    """PnL-style metrics computed from per-step rewards."""

    gross_profit: float
    gross_loss: float
    profit_factor: float
    max_drawdown: float


def calculate_reward_metrics(rewards: tuple[float, ...] | list[float]) -> RewardMetrics:
    gross_profit = sum(reward for reward in rewards if reward > 0.0)
    gross_loss = -sum(reward for reward in rewards if reward < 0.0)
    profit_factor = gross_profit / gross_loss if gross_loss else float("inf")

    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for reward in rewards:
        equity += reward
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)

    return RewardMetrics(
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
    )

