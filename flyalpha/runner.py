"""Central command runner for FlyAlpha."""

from __future__ import annotations

import argparse

from flyalpha.data import load_candles_csv
from flyalpha.environment import MoneyManagementConfig
from flyalpha.experiments.ablation import run_ablation_suite
from flyalpha.experiments.credit import run_credit_assignment_grid
from flyalpha.experiments.reporting import create_run_dir, write_json, write_rows_csv
from flyalpha.experiments.stats import summarize
from flyalpha.experiments.stats import summarize_csv
from flyalpha.experiments.strategy import StrategyFilterConfig
from flyalpha.experiments.tuning import format_tuning_report, format_validation_report, run_train_test_validation, run_tuning_grid
from flyalpha.experiments.walk_forward import run_walk_forward
from flyalpha.actions import TradingAction
from flyalpha.trading_loop import run_trading_once


def _parse_float_grid(raw: str) -> tuple[float, ...]:
    return tuple(float(value.strip()) for value in raw.split(",") if value.strip())


def _parse_optional_float_grid(raw: str) -> tuple[float | None, ...]:
    values: list[float | None] = []
    for value in raw.split(","):
        cleaned = value.strip().lower()
        if not cleaned:
            continue
        values.append(None if cleaned in {"none", "off", "0"} else float(cleaned))
    return tuple(values)


def _parse_int_grid(raw: str) -> tuple[int, ...]:
    return tuple(int(value.strip()) for value in raw.split(",") if value.strip())


def _parse_bool_grid(raw: str) -> tuple[bool, ...]:
    values: list[bool] = []
    for value in raw.split(","):
        cleaned = value.strip().lower()
        if not cleaned:
            continue
        values.append(cleaned in {"1", "true", "yes", "y", "on"})
    return tuple(values)


def _parse_int_csv(raw: str) -> tuple[int, ...]:
    return tuple(int(value.strip()) for value in raw.split(",") if value.strip())


def _flatten_summary(prefix: str, summary: dict) -> dict:
    return {f"{prefix}_{key}": value for key, value in summary.items()}


def _money_management_from_args(args: argparse.Namespace) -> MoneyManagementConfig | None:
    if getattr(args, "no_money_management", False):
        return None
    return MoneyManagementConfig(
        initial_equity=args.initial_equity,
        risk_per_trade=args.risk_per_trade,
        stop_loss_pct=args.stop_loss_pct,
        take_profit_pct=args.take_profit_pct,
        max_position_fraction=args.max_position_fraction,
        max_leverage=args.max_leverage,
        cost_bps=args.cost_bps,
        min_quantity=args.min_quantity,
        breakeven_trigger_pct=args.breakeven_trigger_pct,
        trailing_stop_pct=args.trailing_stop_pct,
    )


def _strategy_filter_from_args(args: argparse.Namespace) -> StrategyFilterConfig:
    return StrategyFilterConfig(
        confidence_threshold=args.confidence_threshold,
        min_volatility=args.min_volatility,
        trend_lookback=args.trend_lookback,
        require_trend_alignment=args.require_trend_alignment,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flyalpha",
        description="Central runner for FlyAlpha experiments, tuning, and trading adapters.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats = subparsers.add_parser("stats", help="Run the conditioning stats report.")
    stats.add_argument("--episodes", type=int, default=12)
    stats.add_argument("--csv", default=None, help="Existing OHLCV CSV to evaluate.")
    stats.add_argument("--limit", type=int, default=None, help="Maximum candles to load from CSV.")
    stats.add_argument("--learning-rate", type=float, default=0.1)
    stats.add_argument("--trace-decay", type=float, default=0.6)
    stats.add_argument("--no-money-management", action="store_true")
    stats.add_argument("--initial-equity", type=float, default=10_000.0)
    stats.add_argument("--risk-per-trade", type=float, default=0.01)
    stats.add_argument("--stop-loss-pct", type=float, default=0.01)
    stats.add_argument("--take-profit-pct", type=float, default=0.02)
    stats.add_argument("--max-position-fraction", type=float, default=1.0)
    stats.add_argument("--max-leverage", type=float, default=1.0)
    stats.add_argument("--cost-bps", type=float, default=1.0)
    stats.add_argument("--min-quantity", type=float, default=0.0)
    stats.add_argument("--breakeven-trigger-pct", type=float, default=None)
    stats.add_argument("--trailing-stop-pct", type=float, default=None)
    stats.add_argument("--confidence-threshold", type=float, default=0.0)
    stats.add_argument("--min-volatility", type=float, default=0.0)
    stats.add_argument("--trend-lookback", type=int, default=1)
    stats.add_argument("--require-trend-alignment", action="store_true")

    tune = subparsers.add_parser("tune", help="Run a deterministic tuning grid.")
    tune.add_argument("--episodes", type=int, default=12)
    tune.add_argument("--limit", type=int, default=10)
    tune.add_argument("--csv", default=None, help="Existing OHLCV CSV to tune against.")
    tune.add_argument("--csv-limit", type=int, default=None, help="Maximum candles to load from CSV.")
    tune.add_argument("--learning-rates", default="0.02,0.05,0.1,0.2")
    tune.add_argument("--trace-decays", default="0.4,0.6,0.8")
    tune.add_argument("--no-money-management", action="store_true")
    tune.add_argument("--initial-equity", type=float, default=10_000.0)
    tune.add_argument("--risk-per-trade", type=float, default=0.01)
    tune.add_argument("--risk-per-trades", default="0.005,0.01,0.02")
    tune.add_argument("--stop-loss-pct", type=float, default=0.01)
    tune.add_argument("--stop-loss-pcts", default="0.005,0.01,0.02")
    tune.add_argument("--take-profit-pct", type=float, default=0.02)
    tune.add_argument("--take-profit-pcts", default="0.01,0.02,0.04")
    tune.add_argument("--max-position-fraction", type=float, default=1.0)
    tune.add_argument("--max-leverage", type=float, default=1.0)
    tune.add_argument("--cost-bps", type=float, default=1.0)
    tune.add_argument("--min-quantity", type=float, default=0.0)
    tune.add_argument("--breakeven-trigger-pct", type=float, default=None)
    tune.add_argument("--breakeven-trigger-pcts", default="none")
    tune.add_argument("--trailing-stop-pct", type=float, default=None)
    tune.add_argument("--trailing-stop-pcts", default="none")
    tune.add_argument("--confidence-thresholds", default="0")
    tune.add_argument("--min-volatilities", default="0")
    tune.add_argument("--trend-lookbacks", default="1")
    tune.add_argument("--trend-alignments", default="false")
    tune.add_argument("--drawdown-penalty", type=float, default=0.25)
    tune.add_argument("--objective", choices=("risk_adjusted", "profit_factor", "return_drawdown", "reward"), default="risk_adjusted")
    tune.add_argument("--min-trades", type=int, default=1)
    tune.add_argument("--no-progress", action="store_true")

    validate = subparsers.add_parser("validate", help="Tune on a CSV train split and evaluate on holdout.")
    validate.add_argument("--csv", required=True)
    validate.add_argument("--csv-limit", type=int, default=None)
    validate.add_argument("--train-fraction", type=float, default=0.7)
    validate.add_argument("--learning-rates", default="0.02,0.05,0.1,0.2")
    validate.add_argument("--trace-decays", default="0.4,0.6,0.8")
    validate.add_argument("--no-money-management", action="store_true")
    validate.add_argument("--initial-equity", type=float, default=10_000.0)
    validate.add_argument("--risk-per-trade", type=float, default=0.01)
    validate.add_argument("--risk-per-trades", default="0.005,0.01,0.02")
    validate.add_argument("--stop-loss-pct", type=float, default=0.01)
    validate.add_argument("--stop-loss-pcts", default="0.005,0.01,0.02")
    validate.add_argument("--take-profit-pct", type=float, default=0.02)
    validate.add_argument("--take-profit-pcts", default="0.01,0.02,0.04")
    validate.add_argument("--max-position-fraction", type=float, default=1.0)
    validate.add_argument("--max-leverage", type=float, default=1.0)
    validate.add_argument("--cost-bps", type=float, default=1.0)
    validate.add_argument("--min-quantity", type=float, default=0.0)
    validate.add_argument("--breakeven-trigger-pct", type=float, default=None)
    validate.add_argument("--breakeven-trigger-pcts", default="none")
    validate.add_argument("--trailing-stop-pct", type=float, default=None)
    validate.add_argument("--trailing-stop-pcts", default="none")
    validate.add_argument("--confidence-thresholds", default="0")
    validate.add_argument("--min-volatilities", default="0")
    validate.add_argument("--trend-lookbacks", default="1")
    validate.add_argument("--trend-alignments", default="false")
    validate.add_argument("--drawdown-penalty", type=float, default=0.25)
    validate.add_argument("--objective", choices=("risk_adjusted", "profit_factor", "return_drawdown", "reward"), default="risk_adjusted")
    validate.add_argument("--min-trades", type=int, default=1)
    validate.add_argument("--no-progress", action="store_true")

    walk = subparsers.add_parser("walk-forward", help="Run repeated train/test windows and save a report.")
    walk.add_argument("--csv", required=True)
    walk.add_argument("--csv-limit", type=int, default=None)
    walk.add_argument("--train-size", type=int, required=True)
    walk.add_argument("--test-size", type=int, required=True)
    walk.add_argument("--step-size", type=int, required=True)
    walk.add_argument("--learning-rates", default="0.02,0.05,0.1")
    walk.add_argument("--trace-decays", default="0.6,0.8")
    walk.add_argument("--initial-equity", type=float, default=10_000.0)
    walk.add_argument("--risk-per-trade", type=float, default=0.001)
    walk.add_argument("--risk-per-trades", default="0.001,0.0025,0.005")
    walk.add_argument("--stop-loss-pct", type=float, default=0.01)
    walk.add_argument("--stop-loss-pcts", default="0.01,0.02")
    walk.add_argument("--take-profit-pct", type=float, default=0.04)
    walk.add_argument("--take-profit-pcts", default="0.01,0.02,0.04")
    walk.add_argument("--max-position-fraction", type=float, default=1.0)
    walk.add_argument("--max-leverage", type=float, default=1.0)
    walk.add_argument("--cost-bps", type=float, default=1.0)
    walk.add_argument("--min-quantity", type=float, default=0.0)
    walk.add_argument("--breakeven-trigger-pct", type=float, default=None)
    walk.add_argument("--trailing-stop-pct", type=float, default=None)
    walk.add_argument("--confidence-threshold", type=float, default=0.0)
    walk.add_argument("--min-volatility", type=float, default=0.0)
    walk.add_argument("--trend-lookback", type=int, default=12)
    walk.add_argument("--require-trend-alignment", action="store_true")
    walk.add_argument("--objective", choices=("risk_adjusted", "profit_factor", "return_drawdown", "reward"), default="profit_factor")
    walk.add_argument("--min-trades", type=int, default=20)
    walk.add_argument("--report-dir", default="runs")
    walk.add_argument("--no-progress", action="store_true")

    ablate = subparsers.add_parser("ablate", help="Run learning-control ablations and save a report.")
    ablate.add_argument("--csv", required=True)
    ablate.add_argument("--csv-limit", type=int, default=None)
    ablate.add_argument("--controls", default="full,dopamine_disabled,plasticity_frozen,random_reward,reward_delay_12,degree_preserving_random")
    ablate.add_argument("--learning-rate", type=float, default=0.05)
    ablate.add_argument("--trace-decay", type=float, default=0.8)
    ablate.add_argument("--initial-equity", type=float, default=10_000.0)
    ablate.add_argument("--risk-per-trade", type=float, default=0.001)
    ablate.add_argument("--stop-loss-pct", type=float, default=0.01)
    ablate.add_argument("--take-profit-pct", type=float, default=0.04)
    ablate.add_argument("--max-position-fraction", type=float, default=1.0)
    ablate.add_argument("--max-leverage", type=float, default=1.0)
    ablate.add_argument("--cost-bps", type=float, default=1.0)
    ablate.add_argument("--min-quantity", type=float, default=0.0)
    ablate.add_argument("--breakeven-trigger-pct", type=float, default=None)
    ablate.add_argument("--trailing-stop-pct", type=float, default=None)
    ablate.add_argument("--confidence-threshold", type=float, default=0.0)
    ablate.add_argument("--min-volatility", type=float, default=0.0)
    ablate.add_argument("--trend-lookback", type=int, default=12)
    ablate.add_argument("--require-trend-alignment", action="store_true")
    ablate.add_argument("--report-dir", default="runs")

    credit = subparsers.add_parser("credit", help="Run reward-delay and trace-decay credit-assignment grid.")
    credit.add_argument("--csv", required=True)
    credit.add_argument("--csv-limit", type=int, default=None)
    credit.add_argument("--reward-delays", default="0,1,3,6,12")
    credit.add_argument("--trace-decays", default="0.4,0.6,0.8,0.95")
    credit.add_argument("--learning-rate", type=float, default=0.05)
    credit.add_argument("--initial-equity", type=float, default=10_000.0)
    credit.add_argument("--risk-per-trade", type=float, default=0.001)
    credit.add_argument("--stop-loss-pct", type=float, default=0.01)
    credit.add_argument("--take-profit-pct", type=float, default=0.04)
    credit.add_argument("--max-position-fraction", type=float, default=1.0)
    credit.add_argument("--max-leverage", type=float, default=1.0)
    credit.add_argument("--cost-bps", type=float, default=1.0)
    credit.add_argument("--min-quantity", type=float, default=0.0)
    credit.add_argument("--breakeven-trigger-pct", type=float, default=None)
    credit.add_argument("--trailing-stop-pct", type=float, default=None)
    credit.add_argument("--confidence-threshold", type=float, default=0.0)
    credit.add_argument("--min-volatility", type=float, default=0.0)
    credit.add_argument("--trend-lookback", type=int, default=12)
    credit.add_argument("--require-trend-alignment", action="store_true")
    credit.add_argument("--report-dir", default="runs")

    trade = subparsers.add_parser("trade", help="Run one paper/live exchange-connected trading tick.")
    trade.add_argument("--mode", choices=("paper", "live"), default="paper")
    trade.add_argument("--symbol", default="BTCUSD")
    trade.add_argument("--action", choices=[action.value for action in TradingAction], default=TradingAction.FLAT.value)
    trade.add_argument("--quantity", type=float, default=0.0)
    trade.add_argument("--base-url", default=None, help="Exchange REST base URL for live mode.")
    trade.add_argument("--i-understand-live-risk", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "stats":
        if args.csv:
            print(
                summarize_csv(
                    csv_path=args.csv,
                    limit=args.limit,
                    learning_rate=args.learning_rate,
                    trace_decay=args.trace_decay,
                    money_management=_money_management_from_args(args),
                    strategy_filter=_strategy_filter_from_args(args),
                )
            )
        else:
            print(summarize(episodes=args.episodes, money_management=_money_management_from_args(args)))
        return

    if args.command == "tune":
        candles = load_candles_csv(args.csv, limit=args.csv_limit) if args.csv else None
        money_management = _money_management_from_args(args)
        trials = run_tuning_grid(
            episodes=args.episodes,
            learning_rates=_parse_float_grid(args.learning_rates),
            trace_decays=_parse_float_grid(args.trace_decays),
            candles=candles,
            money_management=money_management,
            risk_per_trades=_parse_float_grid(args.risk_per_trades) if money_management else None,
            stop_loss_pcts=_parse_float_grid(args.stop_loss_pcts) if money_management else None,
            take_profit_pcts=_parse_optional_float_grid(args.take_profit_pcts) if money_management else None,
            confidence_thresholds=_parse_float_grid(args.confidence_thresholds),
            min_volatilities=_parse_float_grid(args.min_volatilities),
            trend_lookbacks=_parse_int_grid(args.trend_lookbacks),
            trend_alignment=_parse_bool_grid(args.trend_alignments),
            breakeven_trigger_pcts=_parse_optional_float_grid(args.breakeven_trigger_pcts) if money_management else None,
            trailing_stop_pcts=_parse_optional_float_grid(args.trailing_stop_pcts) if money_management else None,
            drawdown_penalty=args.drawdown_penalty,
            objective=args.objective,
            min_trades=args.min_trades,
            show_progress=not args.no_progress,
        )
        print(format_tuning_report(trials, limit=args.limit))
        return

    if args.command == "trade":
        result = run_trading_once(
            mode=args.mode,
            symbol=args.symbol,
            action=TradingAction(args.action),
            quantity=args.quantity,
            base_url=args.base_url,
            live_confirmed=args.i_understand_live_risk,
        )
        print("FlyAlpha trading tick")
        print("=====================")
        print(f"Mode:       {result.mode}")
        print(f"Symbol:     {result.symbol}")
        print(f"Last price: {result.last_price:.4f}")
        print(f"Action:     {result.action.value}")
        print(f"Order:      {result.order}")
        return

    if args.command == "validate":
        candles = load_candles_csv(args.csv, limit=args.csv_limit)
        money_management = _money_management_from_args(args)
        result = run_train_test_validation(
            candles=candles,
            train_fraction=args.train_fraction,
            learning_rates=_parse_float_grid(args.learning_rates),
            trace_decays=_parse_float_grid(args.trace_decays),
            money_management=money_management,
            risk_per_trades=_parse_float_grid(args.risk_per_trades) if money_management else None,
            stop_loss_pcts=_parse_float_grid(args.stop_loss_pcts) if money_management else None,
            take_profit_pcts=_parse_optional_float_grid(args.take_profit_pcts) if money_management else None,
            confidence_thresholds=_parse_float_grid(args.confidence_thresholds),
            min_volatilities=_parse_float_grid(args.min_volatilities),
            trend_lookbacks=_parse_int_grid(args.trend_lookbacks),
            trend_alignment=_parse_bool_grid(args.trend_alignments),
            breakeven_trigger_pcts=_parse_optional_float_grid(args.breakeven_trigger_pcts) if money_management else None,
            trailing_stop_pcts=_parse_optional_float_grid(args.trailing_stop_pcts) if money_management else None,
            drawdown_penalty=args.drawdown_penalty,
            objective=args.objective,
            min_trades=args.min_trades,
            show_progress=not args.no_progress,
        )
        print(format_validation_report(result))
        return

    if args.command == "walk-forward":
        candles = load_candles_csv(args.csv, limit=args.csv_limit)
        money_management = _money_management_from_args(args)
        strategy_filter = _strategy_filter_from_args(args)
        windows = run_walk_forward(
            candles=candles,
            train_size=args.train_size,
            test_size=args.test_size,
            step_size=args.step_size,
            learning_rates=_parse_float_grid(args.learning_rates),
            trace_decays=_parse_float_grid(args.trace_decays),
            money_management=money_management,
            strategy_filter=strategy_filter,
            risk_per_trades=_parse_float_grid(args.risk_per_trades),
            stop_loss_pcts=_parse_float_grid(args.stop_loss_pcts),
            take_profit_pcts=_parse_optional_float_grid(args.take_profit_pcts),
            objective=args.objective,
            min_trades=args.min_trades,
            show_progress=not args.no_progress,
        )
        run_dir = create_run_dir(args.report_dir, "walk_forward")
        rows = [
            {
                "window": window.index,
                "train_start": window.train_start,
                "train_end": window.train_end,
                "test_start": window.test_start,
                "test_end": window.test_end,
                "lr": window.train_best.learning_rate,
                "decay": window.train_best.trace_decay,
                "risk": window.train_best.risk_per_trade,
                "stop": window.train_best.stop_loss_pct,
                "tp": window.train_best.take_profit_pct,
                **_flatten_summary("test", window.test_summary),
            }
            for window in windows
        ]
        write_rows_csv(run_dir / "walk_forward.csv", rows)
        write_json(run_dir / "summary.json", {"command": "walk-forward", "windows": rows})
        print(f"Saved walk-forward report: {run_dir}")
        for row in rows:
            print(
                f"window {row['window']}: test_pf={row['test_profit_factor']:.4f} "
                f"test_reward={row['test_cumulative_reward']:.4f} test_mdd={row['test_max_drawdown']:.4f}"
            )
        return

    if args.command == "ablate":
        candles = load_candles_csv(args.csv, limit=args.csv_limit)
        rows = run_ablation_suite(
            candles=candles,
            controls=tuple(control.strip() for control in args.controls.split(",") if control.strip()),
            learning_rate=args.learning_rate,
            trace_decay=args.trace_decay,
            money_management=_money_management_from_args(args),
            strategy_filter=_strategy_filter_from_args(args),
        )
        run_dir = create_run_dir(args.report_dir, "ablation")
        flat_rows = [{"control": row.control, **row.summary} for row in rows]
        write_rows_csv(run_dir / "ablations.csv", flat_rows)
        write_json(run_dir / "summary.json", {"command": "ablate", "rows": flat_rows})
        print(f"Saved ablation report: {run_dir}")
        for row in flat_rows:
            if "profit_factor" in row:
                print(f"{row['control']}: pf={row['profit_factor']:.4f} reward={row['cumulative_reward']:.4f} mdd={row['max_drawdown']:.4f}")
            else:
                print(f"{row['control']}: {row.get('note')}")
        return

    if args.command == "credit":
        candles = load_candles_csv(args.csv, limit=args.csv_limit)
        rows = run_credit_assignment_grid(
            candles=candles,
            reward_delays=_parse_int_csv(args.reward_delays),
            trace_decays=_parse_float_grid(args.trace_decays),
            learning_rate=args.learning_rate,
            money_management=_money_management_from_args(args),
            strategy_filter=_strategy_filter_from_args(args),
        )
        run_dir = create_run_dir(args.report_dir, "credit")
        flat_rows = [
            {"reward_delay": row.reward_delay, "trace_decay": row.trace_decay, **row.summary}
            for row in rows
        ]
        write_rows_csv(run_dir / "credit_assignment.csv", flat_rows)
        write_json(run_dir / "summary.json", {"command": "credit", "rows": flat_rows})
        print(f"Saved credit-assignment report: {run_dir}")
        for row in flat_rows:
            print(
                f"delay={row['reward_delay']} trace={row['trace_decay']}: "
                f"pf={row['profit_factor']:.4f} reward={row['cumulative_reward']:.4f} mdd={row['max_drawdown']:.4f}"
            )
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
