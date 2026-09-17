"""Persist reproducible run reports."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flyalpha.experiments.conditioning import ConditioningResult
from flyalpha.experiments.metrics import calculate_reward_metrics


def create_run_dir(root: str | Path = "runs", prefix: str = "run") -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = Path(root) / f"{stamp}_{prefix}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def result_summary(result: ConditioningResult) -> dict[str, Any]:
    metrics = calculate_reward_metrics(result.rewards)
    active = [(reward, action) for reward, action in zip(result.rewards, result.actions) if action.value != "FLAT"]
    active_wins = sum(1 for reward, _ in active if reward > 0.0)
    return {
        "episodes": len(result.rewards),
        "cumulative_reward": result.cumulative_reward,
        "final_equity": result.equity_curve[-1] if result.equity_curve else None,
        "profit_factor": metrics.profit_factor,
        "max_drawdown": metrics.max_drawdown,
        "gross_profit": metrics.gross_profit,
        "gross_loss": metrics.gross_loss,
        "active_trades": len(active),
        "active_win_rate": active_wins / len(active) if active else 0.0,
        "learned_weights": len(result.learned_weights),
    }


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n")


def write_equity_curve(path: str | Path, result: ConditioningResult) -> None:
    with Path(path).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["step", "reward", "equity", "action", "quantity"])
        for index, reward in enumerate(result.rewards):
            equity = result.equity_curve[index] if index < len(result.equity_curve) else ""
            quantity = result.quantities[index] if index < len(result.quantities) else ""
            writer.writerow([index, reward, equity, result.actions[index].value, quantity])


def write_rows_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        Path(path).write_text("")
        return
    fieldnames = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value
