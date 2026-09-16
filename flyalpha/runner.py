"""Central command runner for FlyAlpha."""

from __future__ import annotations

import argparse

from flyalpha.data import load_candles_csv
from flyalpha.environment import MoneyManagementConfig
from flyalpha.experiments.stats import summarize
from flyalpha.experiments.stats import summarize_csv
from flyalpha.experiments.tuning import format_tuning_report, format_validation_report, run_train_test_validation, run_tuning_grid
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
    tune.add_argument("--drawdown-penalty", type=float, default=0.25)

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
    validate.add_argument("--drawdown-penalty", type=float, default=0.25)

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
            drawdown_penalty=args.drawdown_penalty,
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
            drawdown_penalty=args.drawdown_penalty,
        )
        print(format_validation_report(result))
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
