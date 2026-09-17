"""Ablation experiments for FlyAlpha learning claims."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.environment import MoneyManagementConfig
from flyalpha.experiments.conditioning import run_conditioning_on_candles
from flyalpha.experiments.controls import LearningControlConfig
from flyalpha.experiments.reporting import result_summary
from flyalpha.experiments.strategy import StrategyFilterConfig
from flyalpha.senses import MarketCandle


@dataclass(frozen=True)
class AblationRow:
    control: str
    summary: dict[str, float | int | None]


CONTROL_CONFIGS = {
    "full": LearningControlConfig(),
    "dopamine_disabled": LearningControlConfig(dopamine_enabled=False),
    "plasticity_frozen": LearningControlConfig(plasticity_enabled=False),
    "random_reward": LearningControlConfig(random_reward=True),
    "reward_delay_12": LearningControlConfig(reward_delay=12),
}


def run_ablation_suite(
    candles: list[MarketCandle],
    controls: tuple[str, ...],
    learning_rate: float,
    trace_decay: float,
    money_management: MoneyManagementConfig,
    strategy_filter: StrategyFilterConfig,
) -> list[AblationRow]:
    rows: list[AblationRow] = []
    for control in controls:
        if control == "degree_preserving_random":
            rows.append(
                AblationRow(
                    control=control,
                    summary={
                        "note": "requires loaded connectome graph; utility is scaffolded separately",
                    },
                )
            )
            continue
        config = CONTROL_CONFIGS[control]
        result = run_conditioning_on_candles(
            candles,
            learning_rate=learning_rate,
            trace_decay=trace_decay,
            money_management=money_management,
            strategy_filter=strategy_filter,
            learning_control=config,
        )
        rows.append(AblationRow(control=control, summary=result_summary(result)))
    return rows

