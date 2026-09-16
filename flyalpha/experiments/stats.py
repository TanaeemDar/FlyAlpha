"""Command-line stats report for the FlyAlpha conditioning demo."""

from __future__ import annotations

import argparse
from collections import Counter

from flyalpha.experiments.conditioning import run_conditioning_demo
from flyalpha.visualization import sparkline


def summarize(episodes: int) -> str:
    result = run_conditioning_demo(episodes=episodes)
    action_counts = Counter(action.value for action in result.actions)
    rewards = result.rewards
    average_reward = sum(rewards) / len(rewards) if rewards else 0.0
    positive_rewards = sum(1 for reward in rewards if reward > 0)
    win_rate = positive_rewards / len(rewards) if rewards else 0.0

    lines = [
        "FlyAlpha conditioning stats",
        "=" * 28,
        f"Episodes:          {episodes}",
        f"Cumulative reward: {result.cumulative_reward:.4f}",
        f"Average reward:    {average_reward:.4f}",
        f"Win rate:          {win_rate:.2%}",
        f"Actions:           {dict(action_counts)}",
        f"Learned weights:   {len(result.learned_weights)}",
        f"Reward trace:      {sparkline(rewards)}",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FlyAlpha's toy conditioning stats report.")
    parser.add_argument("--episodes", type=int, default=12, help="Number of conditioning episodes to run.")
    args = parser.parse_args()
    print(summarize(episodes=args.episodes))


if __name__ == "__main__":
    main()

