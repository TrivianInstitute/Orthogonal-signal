import pytest

from orthogonal_signal.governance.generative_differentiation import (
    DifferentiationState,
    crystallization_risk,
    orthogonal_reserve_delta,
)


def state(**overrides):
    values = dict(
        constraint_diversity=0.8,
        representational_diversity=0.8,
        attractor_concentration=0.2,
        orthogonal_reserve=0.8,
        novelty_velocity=0.8,
        temporal_mode_diversity=0.8,
    )
    values.update(overrides)
    return DifferentiationState(**values)


def test_preservation_floor_is_non_compensatory():
    assert state(novelty_velocity=0.05).preservation_floor == pytest.approx(0.05)


def test_attractor_concentration_reduces_preserved_difference():
    assert state(attractor_concentration=0.9).preservation_floor == pytest.approx(0.1)


def test_crystallization_risk_uses_declared_floor():
    assert crystallization_risk(state(orthogonal_reserve=0.2), floor=0.4)
    assert not crystallization_risk(state(), floor=0.4)


def test_orthogonal_reserve_delta_tracks_loss_and_renewal():
    assert orthogonal_reserve_delta(state(orthogonal_reserve=0.8), state(orthogonal_reserve=0.3)) == pytest.approx(-0.5)
    assert orthogonal_reserve_delta(state(orthogonal_reserve=0.2), state(orthogonal_reserve=0.7)) == pytest.approx(0.5)


def test_invalid_dimension_is_rejected():
    with pytest.raises(ValueError):
        state(constraint_diversity=1.1)


def test_invalid_floor_is_rejected():
    with pytest.raises(ValueError):
        crystallization_risk(state(), floor=-0.1)
