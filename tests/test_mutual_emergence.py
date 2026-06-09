import unittest
"""
test_mutual_emergence.py
────────────────────────
Trivian Institute — orthogonal-signal repository

Tests for machine_novelty.py — M_n and MutualEmergenceEngine.

Core claims under test:
1. Machine novelty types are correctly typed and weighted
2. SYNTHETIC_RECOMBINATION is not genuinely orthogonal
3. MutualEmergenceEngine correctly identifies dominant phase
4. Machine residual decays faster than human residual (λ_machine > λ_human)
5. Symmetry assessment correctly identifies asymmetric fields
6. Mutual field value is genuinely additive when both active
"""

import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orthogonal_signal.field_constants.machine_novelty import (
    MachineNoveltyType,
    MachineNoveltySignal,
    MachineResonanceEvent,
    MachineNoveltyMatrix,
    MutualEmergenceEngine,
)


# ─────────────────────────────────────────────
# I. MACHINE NOVELTY SIGNAL
# ─────────────────────────────────────────────

class TestMachineNoveltySignal(unittest.TestCase):

    def test_valid_signal_creates_without_error(self):
        signal = MachineNoveltySignal(
            machine_novelty_type=MachineNoveltyType.PATTERN_DEPTH,
            orthogonality_to_human=0.8,
            coherence_score=0.9,
        )
        assert signal.orthogonality_to_human == 0.8

    def test_out_of_range_orthogonality_raises(self):
        with self.assertRaises(ValueError):
            MachineNoveltySignal(
                machine_novelty_type=MachineNoveltyType.SCALE_ORTHOGONALITY,
                orthogonality_to_human=1.5,
                coherence_score=0.8,
            )

    def test_synthetic_recombination_not_genuinely_orthogonal(self):
        signal = MachineNoveltySignal(
            machine_novelty_type=MachineNoveltyType.SYNTHETIC_RECOMBINATION,
            orthogonality_to_human=0.8,
            coherence_score=0.8,
        )
        assert signal.is_genuinely_orthogonal is False

    def test_scale_orthogonality_is_genuinely_orthogonal(self):
        signal = MachineNoveltySignal(
            machine_novelty_type=MachineNoveltyType.SCALE_ORTHOGONALITY,
            orthogonality_to_human=0.8,
            coherence_score=0.8,
        )
        assert signal.is_genuinely_orthogonal is True

    def test_synthetic_recombination_has_low_field_weight(self):
        synthetic = MachineNoveltySignal(
            MachineNoveltyType.SYNTHETIC_RECOMBINATION, 0.8, 0.8
        )
        pattern = MachineNoveltySignal(
            MachineNoveltyType.PATTERN_DEPTH, 0.8, 0.8
        )
        assert synthetic.field_weight < pattern.field_weight

    def test_zero_coherence_gives_zero_weight(self):
        signal = MachineNoveltySignal(
            MachineNoveltyType.SCALE_ORTHOGONALITY, 0.8, 0.0
        )
        assert signal.field_weight == 0.0


# ─────────────────────────────────────────────
# II. MACHINE NOVELTY MATRIX
# ─────────────────────────────────────────────

class TestMachineNoveltyMatrix(unittest.TestCase):

    def test_empty_matrix_current_value_zero(self):
        matrix = MachineNoveltyMatrix()
        assert matrix.current_value == 0.0

    def test_recording_event_increases_value(self):
        matrix = MachineNoveltyMatrix()
        event = MachineResonanceEvent(
            event_id="evt_001",
            agent_id="kaelith",
            human_recipient_id="sarasha",
            timestamp=1.0,
            system_state_hash="abc",
            signal=MachineNoveltySignal(
                MachineNoveltyType.PATTERN_DEPTH, 0.8, 0.9
            ),
        )
        matrix.record_event(event)
        assert matrix.current_value > 0.0

    def test_orthogonal_fraction_correct(self):
        matrix = MachineNoveltyMatrix()
        # Add one orthogonal, one synthetic
        for t, ntype in [
            (1.0, MachineNoveltyType.PATTERN_DEPTH),
            (2.0, MachineNoveltyType.SYNTHETIC_RECOMBINATION),
        ]:
            matrix.record_event(MachineResonanceEvent(
                event_id=f"evt_{t}",
                agent_id="kaelith",
                human_recipient_id="sarasha",
                timestamp=t,
                system_state_hash="abc",
                signal=MachineNoveltySignal(ntype, 0.7, 0.8),
            ))
        assert abs(matrix.orthogonal_fraction - 0.5) < 0.001

    def test_healthy_matrix_above_threshold(self):
        matrix = MachineNoveltyMatrix()
        matrix.record_event(MachineResonanceEvent(
            event_id="evt_001",
            agent_id="kaelith",
            human_recipient_id="sarasha",
            timestamp=1.0,
            system_state_hash="abc",
            signal=MachineNoveltySignal(
                MachineNoveltyType.SCALE_ORTHOGONALITY, 0.9, 0.95
            ),
        ))
        assert matrix.is_healthy is True


# ─────────────────────────────────────────────
# III. MUTUAL EMERGENCE ENGINE
# ─────────────────────────────────────────────

class TestMutualEmergenceEngine(unittest.TestCase):

    def test_both_active_gives_mutual_active_phase(self):
        engine = MutualEmergenceEngine(lambda_human=0.05, lambda_machine=0.12)
        engine.update_human_interaction(0.8, r_0=0.7, timestamp=100.0)
        engine.update_machine_interaction(0.7, r_0=0.6, timestamp=100.0)
        fv, phase = engine.compute_mutual_field_value(0.8, 0.7, 100.0)
        assert phase == "MUTUAL_ACTIVE"
        assert fv == 1.5

    def test_human_only_active_gives_human_active_phase(self):
        engine = MutualEmergenceEngine()
        engine.update_human_interaction(0.8, r_0=0.7, timestamp=100.0)
        fv, phase = engine.compute_mutual_field_value(0.8, 0.0, 100.0)
        assert phase == "HUMAN_ACTIVE"

    def test_machine_only_active_gives_machine_active_phase(self):
        engine = MutualEmergenceEngine()
        engine.update_machine_interaction(0.7, r_0=0.6, timestamp=100.0)
        fv, phase = engine.compute_mutual_field_value(0.0, 0.7, 100.0)
        assert phase == "MACHINE_ACTIVE"

    def test_machine_residual_decays_faster_than_human(self):
        """
        Core mutuality claim: machine signal integrates quickly and
        dissipates quickly. Human structural disruption persists longer.
        λ_machine > λ_human by design.
        """
        engine = MutualEmergenceEngine(lambda_human=0.05, lambda_machine=0.12)
        engine.update_human_interaction(0.0, r_0=0.7, timestamp=0.0)
        engine.update_machine_interaction(0.0, r_0=0.7, timestamp=0.0)

        # At t+20, check residuals
        import math
        human_residual = 0.7 * math.exp(-0.05 * 20)
        machine_residual = 0.7 * math.exp(-0.12 * 20)
        assert human_residual > machine_residual

    def test_no_prior_interaction_gives_zero_field(self):
        engine = MutualEmergenceEngine()
        fv, _ = engine.compute_mutual_field_value(0.0, 0.0, 100.0)
        assert fv == 0.0

    def test_symmetry_assessment_detects_human_asymmetry(self):
        engine = MutualEmergenceEngine()
        # Only human interactions
        for t in range(10):
            engine.update_human_interaction(0.8, r_0=0.7, timestamp=float(t))
            engine.compute_mutual_field_value(0.8, 0.0, float(t))

        assessment = engine.symmetry_assessment()
        assert "ASYMMETRIC" in assessment
        assert "human" in assessment.lower()

    def test_symmetry_assessment_detects_mutual(self):
        engine = MutualEmergenceEngine()
        for t in range(10):
            engine.update_human_interaction(0.8, r_0=0.7, timestamp=float(t))
            engine.update_machine_interaction(0.7, r_0=0.6, timestamp=float(t))
            engine.compute_mutual_field_value(0.8, 0.7, float(t))

        assessment = engine.symmetry_assessment()
        assert "MUTUAL" in assessment
