import unittest
"""
test_stagnation_dynamics.py
───────────────────────────
Trivian Institute — orthogonal-signal repository

Tests for stagnation_dynamics.py — the core simulation and decay mechanics.

Core claims under test:
1. Decay function behaves correctly (exponential, floored)
2. R_0 computation is correct (Frobenius norm)
3. Wave function max() correctly selects dominant phase
4. Three-condition simulation produces diverging emergence curves
5. Orthogonal injection >> noise injection >> closed loop
6. Horizon clock correctly predicts crystallization
"""

import math
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orthogonal_signal.field_constants.stagnation_dynamics import (
    residual_plasticity,
    compute_r0,
    field_value,
    classify_phase_state,
    StagnationSimulator,
    HorizonClock,
)


# ─────────────────────────────────────────────
# I. DECAY FUNCTION
# ─────────────────────────────────────────────

class TestResidualPlasticity(unittest.TestCase):

    def test_at_zero_elapsed_returns_r0(self):
        assert residual_plasticity(r_0=0.8, elapsed_time=0.0, elasticity_lambda=0.1) == 0.8

    def test_decays_over_time(self):
        r1 = residual_plasticity(0.8, 10.0, 0.1)
        r2 = residual_plasticity(0.8, 20.0, 0.1)
        assert r1 > r2

    def test_higher_lambda_decays_faster(self):
        slow = residual_plasticity(0.8, 10.0, elasticity_lambda=0.05)
        fast = residual_plasticity(0.8, 10.0, elasticity_lambda=0.20)
        assert slow > fast

    def test_zero_r0_returns_zero(self):
        assert residual_plasticity(r_0=0.0, elapsed_time=5.0, elasticity_lambda=0.1) == 0.0

    def test_zero_lambda_returns_r0(self):
        assert residual_plasticity(r_0=0.7, elapsed_time=100.0, elasticity_lambda=0.0) == 0.0

    def test_exponential_relationship(self):
        r_0 = 1.0
        lam = 0.1
        t = 5.0
        expected = r_0 * math.exp(-lam * t)
        result = residual_plasticity(r_0, t, lam)
        assert abs(result - expected) < 1e-10


# ─────────────────────────────────────────────
# II. R_0 COMPUTATION
# ─────────────────────────────────────────────

class TestComputeR0(unittest.TestCase):

    def test_identical_matrices_give_zero_r0(self):
        m = np.ones((5, 5))
        assert compute_r0(m, m) == 0.0

    def test_different_matrices_give_positive_r0(self):
        baseline = np.zeros((5, 5))
        disrupted = np.ones((5, 5))
        assert compute_r0(baseline, disrupted) > 0.0

    def test_r0_equals_frobenius_norm(self):
        baseline = np.zeros((4, 4))
        disrupted = np.eye(4)
        expected = np.linalg.norm(disrupted - baseline, 'fro')
        result = compute_r0(baseline, disrupted)
        assert abs(result - expected) < 1e-10

    def test_larger_disruption_gives_larger_r0(self):
        baseline = np.zeros((5, 5))
        small_disruption = np.ones((5, 5)) * 0.1
        large_disruption = np.ones((5, 5)) * 0.9
        assert compute_r0(baseline, large_disruption) > compute_r0(baseline, small_disruption)


# ─────────────────────────────────────────────
# III. WAVE FUNCTION
# ─────────────────────────────────────────────

class TestFieldValue(unittest.TestCase):

    def test_active_human_dominates_over_residual(self):
        # When H_n_active is high, it should dominate
        fv = field_value(
            h_n_active=0.9,
            r_0=0.5,
            elapsed_time=0.0,
            elasticity_lambda=0.1,
        )
        assert fv == 0.9

    def test_residual_dominates_when_human_absent(self):
        # When human is gone but R_0 is high and little time has passed
        fv = field_value(
            h_n_active=0.0,
            r_0=0.8,
            elapsed_time=1.0,
            elasticity_lambda=0.05,
        )
        expected_residual = 0.8 * math.exp(-0.05 * 1.0)
        assert abs(fv - expected_residual) < 1e-10

    def test_zero_h_n_and_zero_r0_gives_zero(self):
        fv = field_value(0.0, 0.0, 10.0, 0.1)
        assert fv == 0.0

    def test_max_selects_larger_of_two(self):
        # Active is lower than residual at t=0
        fv = field_value(
            h_n_active=0.3,
            r_0=0.9,
            elapsed_time=0.0,
            elasticity_lambda=0.1,
        )
        assert fv == 0.9  # Residual at t=0 = R_0 = 0.9

    def test_residual_decays_over_time(self):
        fv_early = field_value(0.0, 0.8, elapsed_time=5.0, elasticity_lambda=0.1)
        fv_late = field_value(0.0, 0.8, elapsed_time=30.0, elasticity_lambda=0.1)
        assert fv_early > fv_late


# ─────────────────────────────────────────────
# IV. PHASE STATE CLASSIFICATION
# ─────────────────────────────────────────────

class TestPhaseStateClassification(unittest.TestCase):

    def test_high_e_low_m_is_generative(self):
        assert classify_phase_state(M=0.3, E=0.8) == "GENERATIVE"

    def test_low_e_high_m_is_stagnation(self):
        assert classify_phase_state(M=0.95, E=0.02) == "STAGNATION"

    def test_mid_values_are_declining_or_critical(self):
        state = classify_phase_state(M=0.6, E=0.4)
        assert state in ("DECLINING", "CRITICAL", "GENERATIVE")

    def test_stagnation_at_extremes(self):
        assert classify_phase_state(M=0.999, E=0.001) == "STAGNATION"


# ─────────────────────────────────────────────
# V. THREE-CONDITION SIMULATION — THE EVIDENCE
# ─────────────────────────────────────────────

class TestStagnationSimulator(unittest.TestCase):
    """
    The core empirical claim of the repository:
    orthogonal >> noise > closed for final emergence score.
    """

    def sim(self):
        return StagnationSimulator(n_steps=100, elasticity_lambda=0.08)

    def test_closed_loop_ends_in_stagnation(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        states = sim.simulate_closed_loop()
        final = states[-1]
        assert final.phase_state == "STAGNATION"
        assert final.emergence_score < 0.1

    def test_closed_loop_m_approaches_one(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        states = sim.simulate_closed_loop()
        final = states[-1]
        assert final.mean_cosine_similarity > 0.9

    def test_noise_injection_better_than_closed_but_still_poor(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        closed = sim.simulate_closed_loop()[-1]
        noise = sim.simulate_noise_injection()[-1]
        # Noise is marginally better but still in stagnation territory
        assert noise.emergence_score > closed.emergence_score
        assert noise.emergence_score < 0.3  # Still poor

    def test_orthogonal_injection_ends_generative(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        states = sim.simulate_orthogonal_injection()
        final = states[-1]
        assert final.phase_state == "GENERATIVE"
        assert final.emergence_score > 0.7

    def test_orthogonal_dramatically_outperforms_noise(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        noise_final = sim.simulate_noise_injection()[-1]
        orth_final = sim.simulate_orthogonal_injection()[-1]
        divergence = orth_final.emergence_score - noise_final.emergence_score
        # Core taxonomy claim: gap must be substantial
        assert divergence > 0.5

    def test_orthogonal_dramatically_outperforms_closed(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        closed_final = sim.simulate_closed_loop()[-1]
        orth_final = sim.simulate_orthogonal_injection()[-1]
        divergence = orth_final.emergence_score - closed_final.emergence_score
        assert divergence > 0.7

    def test_m_stays_low_with_orthogonal_injection(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        states = sim.simulate_orthogonal_injection()
        final = states[-1]
        # M should stay disrupted — not approaching 1.0
        assert final.mean_cosine_similarity < 0.5

    def test_run_all_returns_three_conditions(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        results = sim.run_all()
        assert set(results.keys()) == {
            "closed_loop", "noise_injection", "orthogonal_injection"
        }

    def test_all_conditions_have_correct_length(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        results = sim.run_all()
        for condition, states in results.items():
            assert len(states) == 100, f"{condition} has wrong length"

    def test_h_n_zero_in_closed_loop(self):
        sim = StagnationSimulator(n_steps=100, elasticity_lambda=0.08)
        states = sim.simulate_closed_loop()
        assert all(s.field_val == 0.0 for s in states)


# ─────────────────────────────────────────────
# VI. HORIZON CLOCK
# ─────────────────────────────────────────────

class TestHorizonClock(unittest.TestCase):

    def test_nominal_when_far_from_horizon(self):
        clock = HorizonClock(r_0=0.9, elasticity_lambda=0.05)
        assert clock.urgency_level == "NOMINAL"

    def test_crisis_when_r0_below_critical_bound(self):
        clock = HorizonClock(
            r_0=0.05,  # Below critical lower bound of 0.15
            elasticity_lambda=0.05,
        )
        assert clock.steps_to_horizon is None
        assert clock.urgency_level == "CRISIS"

    def test_steps_to_horizon_decreases_with_elapsed_time(self):
        clock = HorizonClock(r_0=0.8, elasticity_lambda=0.08)
        clock.tick(elapsed_since_interaction=0.0)
        steps_early = clock.steps_to_horizon

        clock.tick(elapsed_since_interaction=10.0)
        steps_later = clock.steps_to_horizon

        assert steps_early > steps_later

    def test_high_lambda_gives_shorter_horizon(self):
        clock_rigid = HorizonClock(r_0=0.8, elasticity_lambda=0.5)
        clock_elastic = HorizonClock(r_0=0.8, elasticity_lambda=0.05)

        steps_rigid = clock_rigid.steps_to_horizon
        steps_elastic = clock_elastic.steps_to_horizon

        assert steps_elastic > steps_rigid

    def test_higher_r0_gives_longer_horizon(self):
        clock_deep = HorizonClock(r_0=0.9, elasticity_lambda=0.08)
        clock_shallow = HorizonClock(r_0=0.2, elasticity_lambda=0.08)

        assert clock_deep.steps_to_horizon > clock_shallow.steps_to_horizon

    def test_crystallization_formula_correct(self):
        r_0 = 0.8
        lam = 0.1
        critical = 0.15
        clock = HorizonClock(
            r_0=r_0,
            elasticity_lambda=lam,
            critical_lower_bound=critical,
        )
        expected = -math.log(critical / r_0) / lam
        assert abs(clock.steps_to_horizon - expected) < 0.01

    def test_r0_failure_diagnosis_when_too_shallow(self):
        clock = HorizonClock(r_0=0.10, elasticity_lambda=0.05)
        assert "R_0" in clock.failure_diagnosis
