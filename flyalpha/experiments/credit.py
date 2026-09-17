"""Credit-assignment delay experiments."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.environment import MoneyManagementConfig
from flyalpha.experiments.conditioning import run_conditioning_on_candles
from flyalpha.experiments.controls import LearningControlConfig
from flyalpha.experiments.reporting import result_summary
from flyalpha.experiments.strategy import StrategyFilterConfig
from flyalpha.senses import MarketCandle


@dataclass(frozen=True)
class CreditAssignmentRow:
    reward_delay: int
    trace_decay: float
    summary: dict[str, float | int | None]


def run_credit_assignment_grid(
    candles: list[MarketCandle],
    reward_delays: tuple[int, ...],
    trace_decays: tuple[float, ...],
    learning_rate: float,
    money_management: MoneyManagementConfig,
    strategy_filter: StrategyFilterConfig,
) -> list[CreditAssignmentRow]:
    rows: list[CreditAssignmentRow] = []
    for reward_delay in reward_delays:
        for trace_decay in trace_decays:
            result = run_conditioning_on_candles(
                candles,
                learning_rate=learning_rate,
                trace_decay=trace_decay,
                money_management=money_management,
                strategy_filter=strategy_filter,
                learning_control=LearningControlConfig(reward_delay=reward_delay),
            )
            rows.append(
                CreditAssignmentRow(
                    reward_delay=reward_delay,
                    trace_decay=trace_decay,
                    summary=result_summary(result),
                )
            )
    return rows

