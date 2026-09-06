"""Generative Differentiation reference primitives for Orthogonal Signal.

Orthogonal Signal is the canonical TRIA research home for measuring independent
constraint origins, orthogonal reserve, crystallization dynamics, and novelty
persistence. These primitives are experimental and intentionally avoid a single
universal "generativity score".
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DifferentiationState:
    constraint_diversity: float
    representational_diversity: float
    attractor_concentration: float
    orthogonal_reserve: float
    novelty_velocity: float
    temporal_mode_diversity: float

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0.0, 1.0]")

    @property
    def preservation_floor(self) -> float:
        """Return the weakest preserved differentiation dimension.

        Attractor concentration is inverted. The minimum operator is deliberate:
        strength elsewhere cannot compensate for collapse of one dimension.
        """
        return min(
            self.constraint_diversity,
            self.representational_diversity,
            1.0 - self.attractor_concentration,
            self.orthogonal_reserve,
            self.novelty_velocity,
            self.temporal_mode_diversity,
        )


def crystallization_risk(
    state: DifferentiationState,
    *,
    floor: float,
) -> bool:
    """Return whether preserved differentiation has fallen below a declared floor.

    The caller owns calibration. `floor` is not a universal scientific threshold.
    """
    if not 0.0 <= floor <= 1.0:
        raise ValueError("floor must be in [0.0, 1.0]")
    return state.preservation_floor < floor


def orthogonal_reserve_delta(
    previous: DifferentiationState,
    current: DifferentiationState,
) -> float:
    """Measure change in access to independent constraint sources."""
    return current.orthogonal_reserve - previous.orthogonal_reserve
