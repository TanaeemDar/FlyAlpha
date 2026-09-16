"""Central command runner for FlyAlpha."""

from __future__ import annotations

import argparse

from flyalpha.experiments.stats import summarize
from flyalpha.experiments.tuning import format_tuning_report, run_tuning_grid


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

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()

