"""Experimental controls for credit assignment and plasticity ablations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningControlConfig:
    """Switches for testing whether learning depends on dopamine timing."""

    dopamine_enabled: bool = True
    plasticity_enabled: bool = True
    reward_delay: int = 0
    random_reward: bool = False
    random_seed: int = 7

