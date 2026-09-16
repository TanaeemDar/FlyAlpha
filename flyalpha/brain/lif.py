"""Leaky integrate-and-fire neuron dynamics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LIFNeuron:
    """A compact LIF unit used to make structural graphs executable."""

    neuron_id: str
    threshold: float = 1.0
    leak: float = 0.1
    reset_potential: float = 0.0
    membrane_potential: float = 0.0

    def step(self, input_current: float) -> bool:
        """Advance one tick and return whether the neuron spiked."""

        self.membrane_potential *= 1.0 - self.leak
        self.membrane_potential += input_current
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = self.reset_potential
            return True
        return False

    def reset(self) -> None:
        self.membrane_potential = self.reset_potential

