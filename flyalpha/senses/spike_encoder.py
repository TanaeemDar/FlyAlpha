"""Map deterministic sensory features to spikes."""

from __future__ import annotations

from dataclasses import dataclass

from .market_encoder import MarketFeatures


@dataclass(frozen=True)
class SpikeEncoder:
    """Threshold encoder for sensory channels."""

    sensitivity: float = 0.01

    def encode(self, features: MarketFeatures) -> list[set[str]]:
        spikes: list[set[str]] = []
        channel_values = {
            "sens_return_pos": features.return_,
            "sens_return_neg": -features.return_,
            "sens_range": features.range_,
            "sens_volume_pos": features.volume_change,
            "sens_volume_neg": -features.volume_change,
            "sens_momentum_pos": features.momentum,
            "sens_momentum_neg": -features.momentum,
            "sens_volatility": features.volatility,
        }
        active = {name for name, value in channel_values.items() if value >= self.sensitivity}
        spikes.append(active)
        spikes.append(set())
        return spikes

