"""Walk-forward validation over repeated train/test windows."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.environment import MoneyManagementConfig
from flyalpha.experiments.reporting import result_summary
from flyalpha.experiments.strategy import StrategyFilterConfig
from flyalpha.experiments.tuning import TuningTrial, run_tuning_grid
from flyalpha.experiments.conditioning import run_conditioning_on_candles
from flyalpha.senses import MarketCandle


@dataclass(frozen=True)
class WalkForwardWindow:
    index: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    train_best: TuningTrial
    test_summary: dict[str, float | int | None]


def run_walk_forward(
    candles: list[MarketCandle],
    train_size: int,
    test_size: int,
    step_size: int,
    learning_rates: tuple[float, ...],
    trace_decays: tuple[float, ...],
    money_management: MoneyManagementConfig,
    strategy_filter: StrategyFilterConfig,
    risk_per_trades: tuple[float, ...],
    stop_loss_pcts: tuple[float, ...],
    take_profit_pcts: tuple[float | None, ...],
    objective: str,
    min_trades: int,
    show_progress: bool,
) -> list[WalkForwardWindow]:
    windows: list[WalkForwardWindow] = []
    start = 0
    index = 1
    while start + train_size + test_size <= len(candles):
        train_start = start
        train_end = start + train_size
        test_start = train_end - 1
        test_end = train_end + test_size
        train = candles[train_start:train_end]
        test = candles[test_start:test_end]
        trials = run_tuning_grid(
            candles=train,
            learning_rates=learning_rates,
            trace_decays=trace_decays,
            money_management=money_management,
            risk_per_trades=risk_per_trades,
            stop_loss_pcts=stop_loss_pcts,
            take_profit_pcts=take_profit_pcts,
            trend_lookbacks=(strategy_filter.trend_lookback,),
            trend_alignment=(strategy_filter.require_trend_alignment,),
            objective=objective,
            min_trades=min_trades,
            show_progress=show_progress,
            progress_label=f"walk {index} train",
        )
        best = trials[0]
        test_management = MoneyManagementConfig(
            initial_equity=money_management.initial_equity,
            risk_per_trade=best.risk_per_trade,
            stop_loss_pct=best.stop_loss_pct,
            take_profit_pct=best.take_profit_pct,
            max_position_fraction=money_management.max_position_fraction,
            max_leverage=money_management.max_leverage,
            cost_bps=money_management.cost_bps,
            min_quantity=money_management.min_quantity,
            breakeven_trigger_pct=best.breakeven_trigger_pct,
            trailing_stop_pct=best.trailing_stop_pct,
        )
        test_filter = StrategyFilterConfig(
            confidence_threshold=best.confidence_threshold,
            min_volatility=best.min_volatility,
            trend_lookback=best.trend_lookback,
            require_trend_alignment=best.require_trend_alignment,
        )
        result = run_conditioning_on_candles(
            test,
            learning_rate=best.learning_rate,
            trace_decay=best.trace_decay,
            money_management=test_management,
            strategy_filter=test_filter,
        )
        windows.append(
            WalkForwardWindow(
                index=index,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                train_best=best,
                test_summary=result_summary(result),
            )
        )
        start += step_size
        index += 1
    return windows

