"""Simple parameter tuning for the conditioning scaffold."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.senses import MarketCandle

from .conditioning import run_conditioning_demo, run_conditioning_on_candles


@dataclass(frozen=True)
class TuningTrial:
    """One conditioning parameter trial."""

    learning_rate: float
    trace_decay: float
    cumulative_reward: float
    learned_weights: int


def run_tuning_grid(
    episodes: int = 12,
    learning_rates: tuple[float, ...] = (0.02, 0.05, 0.1, 0.2),
    trace_decays: tuple[float, ...] = (0.4, 0.6, 0.8),
    candles: list[MarketCandle] | None = None,
) -> list[TuningTrial]:
    """Run a deterministic grid over mushroom-body plasticity parameters."""

    trials: list[TuningTrial] = []
    for learning_rate in learning_rates:
        for trace_decay in trace_decays:
            if candles is None:
                result = run_conditioning_demo(
                    episodes=episodes,
                    learning_rate=learning_rate,
                    trace_decay=trace_decay,
                )
            else:
                result = run_conditioning_on_candles(
                    candles,
                    learning_rate=learning_rate,
                    trace_decay=trace_decay,
                )
            trials.append(
                TuningTrial(
                    learning_rate=learning_rate,
                    trace_decay=trace_decay,
                    cumulative_reward=result.cumulative_reward,
                    learned_weights=len(result.learned_weights),
                )
            )
    return sorted(trials, key=lambda trial: trial.cumulative_reward, reverse=True)


def format_tuning_report(trials: list[TuningTrial], limit: int = 10) -> str:
    """Format tuning results as a compact terminal table."""

    lines = [
        "FlyAlpha tuning report",
        "=" * 23,
        "rank  lr      decay   reward    weights",
    ]
    for rank, trial in enumerate(trials[:limit], start=1):
        lines.append(
            f"{rank:<5} {trial.learning_rate:<7.3f} {trial.trace_decay:<7.3f} "
            f"{trial.cumulative_reward:<9.4f} {trial.learned_weights}"
        )
    return "\n".join(lines)
