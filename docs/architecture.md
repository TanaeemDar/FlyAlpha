# Architecture

```text
Market candles
    |
    v
Deterministic feature normalization
    |
    v
Spike encoder
    |
    v
Fly-inspired LIF graph
    |
    v
Kenyon cells -> dopamine-gated KC-to-MBON plasticity
    |
    v
MBON output populations
    |
    v
LONG / SHORT / FLAT
```

The code is intentionally small and inspectable. Each layer can be swapped for
a richer implementation while preserving the same scientific boundary: decisions
come from fly-inspired neural dynamics, and learning is localized to the
mushroom-body plasticity module.

