"""Command-line stats report for the FlyAlpha conditioning demo."""

from __future__ import annotations

import argparse
from collections import Counter

from flyalpha.data import load_candles_csv
from flyalpha.experiments.conditioning import ConditioningResult, run_conditioning_demo, run_conditioning_on_candles
from flyalpha.visualization import sparkline


def _format_summary(result: ConditioningResult, label: str) -> str:
    action_counts = Counter(action.value for action in result.actions)
    rewards = result.rewards
    average_reward = sum(rewards) / len(rewards) if rewards else 0.0
    positive_rewards = sum(1 for reward in rewards if reward > 0)
    win_rate = positive_rewards / len(rewards) if rewards else 0.0

    lines = [
        "FlyAlpha conditioning stats",
        "=" * 28,
        f"Dataset:           {label}",
        f"Episodes:          {len(rewards)}",
        f"Cumulative reward: {result.cumulative_reward:.4f}",
        f"Average reward:    {average_reward:.4f}",
        f"Win rate:          {win_rate:.2%}",
        f"Actions:           {dict(action_counts)}",
        f"Learned weights:   {len(result.learned_weights)}",
        f"Reward trace:      {sparkline(rewards)}",
    ]
    return "\n".join(lines)


def summarize(episodes: int) -> str:
    return _format_summary(run_conditioning_demo(episodes=episodes), label="toy-conditioning")


def summarize_csv(
    csv_path: str,
    limit: int | None = None,
    learning_rate: float = 0.1,
    trace_decay: float = 0.6,
) -> str:
    candles = load_candles_csv(csv_path, limit=limit)
    result = run_conditioning_on_candles(
        candles,
        learning_rate=learning_rate,
        trace_decay=trace_decay,
    )
    return _format_summary(result, label=csv_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FlyAlpha's toy conditioning stats report.")
    parser.add_argument("--episodes", type=int, default=12, help="Number of conditioning episodes to run.")
    parser.add_argument("--csv", default=None, help="Existing OHLCV CSV to evaluate.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum candles to load from CSV.")
    args = parser.parse_args()
    if args.csv:
        print(summarize_csv(csv_path=args.csv, limit=args.limit))
    else:
        print(summarize(episodes=args.episodes))


if __name__ == "__main__":
    main()
