"""Small dependency-free visual helpers."""

from __future__ import annotations


def sparkline(values: list[float] | tuple[float, ...], width: int = 80) -> str:
    """Render numeric values as a bounded ASCII learning trace."""

    if not values:
        return ""
    values = _downsample(values, width=width)
    low = min(values)
    high = max(values)
    if high == low:
        return "-" * len(values)
    glyphs = "._-=+*#%@"
    return "".join(glyphs[round((value - low) / (high - low) * (len(glyphs) - 1))] for value in values)


def _downsample(values: list[float] | tuple[float, ...], width: int) -> list[float] | tuple[float, ...]:
    if width <= 0 or len(values) <= width:
        return values

    bucket_size = len(values) / width
    sampled: list[float] = []
    for index in range(width):
        start = round(index * bucket_size)
        end = round((index + 1) * bucket_size)
        bucket = values[start:end] or values[start : start + 1]
        sampled.append(sum(bucket) / len(bucket))
    return sampled
