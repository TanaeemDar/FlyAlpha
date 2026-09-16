"""MBON population readout."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MBONReadout:
    """Approach, avoidance, and hold activity from output populations."""

    approach: float
    avoidance: float
    hold: float = 0.0

    @property
    def dominant_population(self) -> str:
        populations = {
            "approach": self.approach,
            "avoidance": self.avoidance,
            "hold": self.hold,
        }
        return max(populations, key=populations.get)

