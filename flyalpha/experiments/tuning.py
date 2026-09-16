"""Simple parameter tuning for the conditioning scaffold."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.environment import MoneyManagementConfig
from flyalpha.experiments.metrics import calculate_reward_metrics
from flyalpha.senses import MarketCandle

from .conditioning import run_conditioning_demo, run_conditioning_on_candles


@dataclass(frozen=True)
class TuningTrial:
    """One conditioning parameter trial."""

    learning_rate: float
    trace_decay: float
    risk_per_trade: float
    stop_loss_pct: float
    take_profit_pct: float | None
    cumulative_reward: float
    profit_factor: float
    max_drawdown: float
    score: float
    learned_weights: int


@dataclass(frozen=True)
class ValidationResult:
    """Train/holdout validation result for selected tuning parameters."""

    train_best: TuningTrial
    test_trial: TuningTrial
    train_candles: int
    test_candles: int


def run_tuning_grid(
    episodes: int = 12,
    learning_rates: tuple[float, ...] = (0.02, 0.05, 0.1, 0.2),
    trace_decays: tuple[float, ...] = (0.4, 0.6, 0.8),
    candles: list[MarketCandle] | None = None,
    money_management: MoneyManagementConfig | None = None,
    risk_per_trades: tuple[float, ...] | None = None,
    stop_loss_pcts: tuple[float, ...] | None = None,
    take_profit_pcts: tuple[float | None, ...] | None = None,
    drawdown_penalty: float = 0.25,
) -> list[TuningTrial]:
    """Run a deterministic grid over mushroom-body plasticity parameters."""

    trials: list[TuningTrial] = []
    for learning_rate in learning_rates:
        for trace_decay in trace_decays:
            for risk_per_trade in risk_per_trades or (money_management.risk_per_trade if money_management else 0.0,):
                for stop_loss_pct in stop_loss_pcts or (money_management.stop_loss_pct if money_management else 0.0,):
                    for take_profit_pct in take_profit_pcts or (money_management.take_profit_pct if money_management else None,):
                        trial_management = None
                        if money_management:
                            trial_management = MoneyManagementConfig(
                                initial_equity=money_management.initial_equity,
                                risk_per_trade=risk_per_trade,
                                stop_loss_pct=stop_loss_pct,
                                take_profit_pct=take_profit_pct,
                                max_position_fraction=money_management.max_position_fraction,
                                max_leverage=money_management.max_leverage,
                                cost_bps=money_management.cost_bps,
                                min_quantity=money_management.min_quantity,
                            )
                        if candles is None:
                            result = run_conditioning_demo(
                                episodes=episodes,
                                learning_rate=learning_rate,
                                trace_decay=trace_decay,
                                money_management=trial_management,
                            )
                        else:
                            result = run_conditioning_on_candles(
                                candles,
                                learning_rate=learning_rate,
                                trace_decay=trace_decay,
                                money_management=trial_management,
                            )
                        metrics = calculate_reward_metrics(result.rewards)
                        score = result.cumulative_reward - drawdown_penalty * metrics.max_drawdown
                        trials.append(
                            TuningTrial(
                                learning_rate=learning_rate,
                                trace_decay=trace_decay,
                                risk_per_trade=risk_per_trade,
                                stop_loss_pct=stop_loss_pct,
                                take_profit_pct=take_profit_pct,
                                cumulative_reward=result.cumulative_reward,
                                profit_factor=metrics.profit_factor,
                                max_drawdown=metrics.max_drawdown,
                                score=score,
                                learned_weights=len(result.learned_weights),
                            )
                        )
    return sorted(trials, key=lambda trial: trial.score, reverse=True)


def format_tuning_report(trials: list[TuningTrial], limit: int = 10) -> str:
    """Format tuning results as a compact terminal table."""

    lines = [
        "FlyAlpha tuning report",
        "=" * 23,
        "rank  lr      decay   risk    stop    tp      reward    pf      mdd       score     weights",
    ]
    for rank, trial in enumerate(trials[:limit], start=1):
        take_profit = "none" if trial.take_profit_pct is None else f"{trial.take_profit_pct:.3f}"
        lines.append(
            f"{rank:<5} {trial.learning_rate:<7.3f} {trial.trace_decay:<7.3f} "
            f"{trial.risk_per_trade:<7.3f} {trial.stop_loss_pct:<7.3f} {take_profit:<7} "
            f"{trial.cumulative_reward:<9.4f} {trial.profit_factor:<7.3f} "
            f"{trial.max_drawdown:<9.4f} {trial.score:<9.4f} {trial.learned_weights}"
        )
    return "\n".join(lines)


def run_train_test_validation(
    candles: list[MarketCandle],
    train_fraction: float = 0.7,
    learning_rates: tuple[float, ...] = (0.02, 0.05, 0.1, 0.2),
    trace_decays: tuple[float, ...] = (0.4, 0.6, 0.8),
    money_management: MoneyManagementConfig | None = None,
    risk_per_trades: tuple[float, ...] | None = None,
    stop_loss_pcts: tuple[float, ...] | None = None,
    take_profit_pcts: tuple[float | None, ...] | None = None,
    drawdown_penalty: float = 0.25,
) -> ValidationResult:
    """Tune on an in-sample slice and evaluate the winner out of sample."""

    if not 0.1 <= train_fraction <= 0.9:
        raise ValueError("train_fraction must be between 0.1 and 0.9")
    split_index = max(2, min(len(candles) - 2, int(len(candles) * train_fraction)))
    train_candles = candles[:split_index]
    test_candles = candles[split_index - 1 :]

    train_trials = run_tuning_grid(
        learning_rates=learning_rates,
        trace_decays=trace_decays,
        candles=train_candles,
        money_management=money_management,
        risk_per_trades=risk_per_trades,
        stop_loss_pcts=stop_loss_pcts,
        take_profit_pcts=take_profit_pcts,
        drawdown_penalty=drawdown_penalty,
    )
    best = train_trials[0]
    test_trials = run_tuning_grid(
        learning_rates=(best.learning_rate,),
        trace_decays=(best.trace_decay,),
        candles=test_candles,
        money_management=money_management,
        risk_per_trades=(best.risk_per_trade,) if money_management else None,
        stop_loss_pcts=(best.stop_loss_pct,) if money_management else None,
        take_profit_pcts=(best.take_profit_pct,) if money_management else None,
        drawdown_penalty=drawdown_penalty,
    )
    return ValidationResult(
        train_best=best,
        test_trial=test_trials[0],
        train_candles=len(train_candles),
        test_candles=len(test_candles),
    )


def format_validation_report(result: ValidationResult) -> str:
    lines = [
        "FlyAlpha train/test validation",
        "=" * 31,
        f"Train candles: {result.train_candles}",
        f"Test candles:  {result.test_candles}",
        "",
        "Selected on train:",
        format_tuning_report([result.train_best], limit=1),
        "",
        "Evaluated on test:",
        format_tuning_report([result.test_trial], limit=1),
    ]
    return "\n".join(lines)
