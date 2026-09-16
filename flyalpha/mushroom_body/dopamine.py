"""PAM/PPL1-inspired dopamine signals."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DopamineSignal:
    """Signed reinforcement signal routed through fly dopamine channels."""

    pam: float = 0.0
    ppl1: float = 0.0

    @classmethod
    def from_prediction_error(cls, rpe: float) -> "DopamineSignal":
        if rpe >= 0.0:
            return cls(pam=rpe, ppl1=0.0)
        return cls(pam=0.0, ppl1=abs(rpe))

    @property
    def signed_value(self) -> float:
        return self.pam - self.ppl1

