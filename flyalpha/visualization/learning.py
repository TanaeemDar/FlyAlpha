"""Small dependency-free visual helpers."""

from __future__ import annotations


def sparkline(values: list[float] | tuple[float, ...]) -> str:
    """Render numeric values as an ASCII learning trace."""

    if not values:
        return ""
    low = min(values)
    high = max(values)
    if high == low:
        return "-" * len(values)
    glyphs = "._-=+*#%@"
    return "".join(glyphs[round((value - low) / (high - low) * (len(glyphs) - 1))] for value in values)

