"""Central command runner for FlyAlpha."""

from __future__ import annotations

import argparse

from flyalpha.data import load_candles_csv
from flyalpha.experiments.stats import summarize
from flyalpha.experiments.stats import summarize_csv
from flyalpha.experiments.tuning import format_tuning_report, run_tuning_grid
from flyalpha.actions import TradingAction
from flyalpha.trading_loop import run_trading_once


def _parse_float_grid(raw: str) -> tuple[float, ...]:
    return tuple(float(value.strip()) for value in raw.split(",") if value.strip())


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

    tune = subparsers.add_parser("tune", help="Run a deterministic tuning grid.")
    tune.add_argument("--episodes", type=int, default=12)
    tune.add_argument("--limit", type=int, default=10)
    tune.add_argument("--csv", default=None, help="Existing OHLCV CSV to tune against.")
    tune.add_argument("--csv-limit", type=int, default=None, help="Maximum candles to load from CSV.")
    tune.add_argument("--learning-rates", default="0.02,0.05,0.1,0.2")
    tune.add_argument("--trace-decays", default="0.4,0.6,0.8")

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
                )
            )
        else:
            print(summarize(episodes=args.episodes))
        return

    if args.command == "tune":
        candles = load_candles_csv(args.csv, limit=args.csv_limit) if args.csv else None
        trials = run_tuning_grid(
            episodes=args.episodes,
            learning_rates=_parse_float_grid(args.learning_rates),
            trace_decays=_parse_float_grid(args.trace_decays),
            candles=candles,
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

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
