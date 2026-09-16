"""Central command runner for FlyAlpha."""

from __future__ import annotations

import argparse

from flyalpha.experiments.stats import summarize
from flyalpha.experiments.tuning import format_tuning_report, run_tuning_grid
from flyalpha.actions import TradingAction
from flyalpha.trading_loop import run_trading_once


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flyalpha",
        description="Central runner for FlyAlpha experiments, tuning, and trading adapters.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats = subparsers.add_parser("stats", help="Run the conditioning stats report.")
    stats.add_argument("--episodes", type=int, default=12)

    tune = subparsers.add_parser("tune", help="Run a deterministic tuning grid.")
    tune.add_argument("--episodes", type=int, default=12)
    tune.add_argument("--limit", type=int, default=10)

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
        print(summarize(episodes=args.episodes))
        return

    if args.command == "tune":
        trials = run_tuning_grid(episodes=args.episodes)
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
