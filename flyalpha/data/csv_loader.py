"""CSV loading for existing OHLCV datasets."""

from __future__ import annotations

import csv
from pathlib import Path

from flyalpha.senses import MarketCandle


REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")


def load_candles_csv(path: str | Path, limit: int | None = None) -> list[MarketCandle]:
    """Load OHLCV candles from a CSV file.

    Column names are matched case-insensitively. Extra columns such as timestamp
    or symbol are ignored.
    """

    csv_path = Path(path)
    candles: list[MarketCandle] = []
    with csv_path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header row: {csv_path}")

        normalized = {field.lower().strip(): field for field in reader.fieldnames}
        missing = [column for column in REQUIRED_COLUMNS if column not in normalized]
        if missing:
            raise ValueError(f"CSV missing required columns {missing}: {csv_path}")

        for row in reader:
            candles.append(
                MarketCandle(
                    open=float(row[normalized["open"]]),
                    high=float(row[normalized["high"]]),
                    low=float(row[normalized["low"]]),
                    close=float(row[normalized["close"]]),
                    volume=float(row[normalized["volume"]]),
                )
            )
            if limit is not None and len(candles) >= limit:
                break

    if len(candles) < 2:
        raise ValueError(f"CSV needs at least two candles: {csv_path}")
    return candles

