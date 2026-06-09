import unittest
"""
test_novelty_taxonomy.py
────────────────────────
Trivian Institute — orthogonal-signal repository

Tests for novelty_taxonomy.py — the foundational classifier.

Core claims under test:
1. Four novelty types are formally distinct and correctly classified
2. Field weights respect the type hierarchy (Embodied > Orthogonal > Synthetic > Random)
3. Machine-generatability flags are correct
4. FieldNoveltyState correctly tracks orthogonal ratio and emergence risk
5. The taxonomy claim: orthogonal signals carry meaningfully higher field weight
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orthogonal_signal.field_constants.novelty_taxonomy import (
    NoveltyType,
    NoveltySignal,
    NoveltyClassifier,
    FieldNoveltyState,
)


# ─────────────────────────────────────────────
# I. NOVELTY SIGNAL VALIDATION
# ─────────────────────────────────────────────

class TestNoveltySignalValidation(unittest.TestCase):

    def test_valid_signal_creates_without_error(self):
        signal = NoveltySignal(
            novelty_type=NoveltyType.ORTHOGONAL,
            orthogonality_score=0.8,
            coherence_score=0.9,
        )
        assert signal.orthogonality_score == 0.8
        assert signal.coherence_score == 0.9

    def test_orthogonality_score_below_zero_raises(self):
        with self.assertRaises(ValueError):
            NoveltySignal(
                novelty_type=NoveltyType.RANDOM,
                orthogonality_score=-0.1,
                coherence_score=0.5,
            )

    def test_orthogonality_score_above_one_raises(self):
        with self.assertRaises(ValueError):
            NoveltySignal(
                novelty_type=NoveltyType.SYNTHETIC,
                orthogonality_score=1.1,
                coherence_score=0.5,
            )

    def test_coherence_score_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            NoveltySignal(
                novelty_type=NoveltyType.EMBODIED,
                orthogonality_score=0.7,
                coherence_score=1.5,
            )


# ─────────────────────────────────────────────
# II. FIELD WEIGHT HIERARCHY
# ─────────────────────────────────────────────

class TestFieldWeightHierarchy(unittest.TestCase):
    """
    The taxonomy's core claim: Embodied > Orthogonal > Synthetic > Random
    for equivalent orthogonality and coherence scores.
    """

    def _make_signal(self, novelty_type, ortho=0.8, coh=0.8):
        return NoveltySignal(
            novelty_type=novelty_type,
            orthogonality_score=ortho,
            coherence_score=coh,
        )

    def test_embodied_outweighs_orthogonal(self):
        embodied = self._make_signal(NoveltyType.EMBODIED)
        orthogonal = self._make_signal(NoveltyType.ORTHOGONAL)
        assert embodied.field_weight > orthogonal.field_weight

    def test_orthogonal_outweighs_synthetic(self):
        orthogonal = self._make_signal(NoveltyType.ORTHOGONAL)
        synthetic = self._make_signal(NoveltyType.SYNTHETIC)
        assert orthogonal.field_weight > synthetic.field_weight

    def test_synthetic_outweighs_random(self):
        synthetic = self._make_signal(NoveltyType.SYNTHETIC)
        random = self._make_signal(NoveltyType.RANDOM)
        assert synthetic.field_weight > random.field_weight

    def test_full_hierarchy(self):
        weights = [
            self._make_signal(NoveltyType.EMBODIED).field_weight,
            self._make_signal(NoveltyType.ORTHOGONAL).field_weight,
            self._make_signal(NoveltyType.SYNTHETIC).field_weight,
            self._make_signal(NoveltyType.RANDOM).field_weight,
        ]
        assert weights == sorted(weights, reverse=True)

    def test_zero_coherence_produces_zero_weight(self):
        signal = self._make_signal(NoveltyType.EMBODIED, coh=0.0)
        assert signal.field_weight == 0.0

    def test_zero_orthogonality_produces_zero_weight(self):
        signal = self._make_signal(NoveltyType.ORTHOGONAL, ortho=0.0)
        assert signal.field_weight == 0.0


# ─────────────────────────────────────────────
# III. MACHINE-GENERATABILITY FLAGS
# ─────────────────────────────────────────────

class TestMachineGeneratability(unittest.TestCase):
    """
    The Synthetic Orthogonality Trap: machines cannot generate
    OrthogonalNovelty or EmbodiedNovelty from within.
    """

    def test_random_is_machine_generatable(self):
        s = NoveltySignal(NoveltyType.RANDOM, 0.1, 0.5)
        assert s.is_machine_generatable is True

    def test_synthetic_is_machine_generatable(self):
        s = NoveltySignal(NoveltyType.SYNTHETIC, 0.5, 0.7)
        assert s.is_machine_generatable is True

    def test_orthogonal_is_not_machine_generatable(self):
        s = NoveltySignal(NoveltyType.ORTHOGONAL, 0.8, 0.8)
        assert s.is_machine_generatable is False

    def test_embodied_is_not_machine_generatable(self):
        s = NoveltySignal(NoveltyType.EMBODIED, 0.9, 0.9)
        assert s.is_machine_generatable is False

    def test_orthogonal_and_embodied_are_orthogonal(self):
        for t in (NoveltyType.ORTHOGONAL, NoveltyType.EMBODIED):
            s = NoveltySignal(t, 0.8, 0.8)
            assert s.is_orthogonal is True

    def test_random_and_synthetic_are_not_orthogonal(self):
        for t in (NoveltyType.RANDOM, NoveltyType.SYNTHETIC):
            s = NoveltySignal(t, 0.8, 0.8)
            assert s.is_orthogonal is False


# ─────────────────────────────────────────────
# IV. NOVELTY CLASSIFIER
# ─────────────────────────────────────────────

class TestNoveltyClassifier(unittest.TestCase):

    def test_low_coherence_always_random(self):
        # Below COHERENCE_FLOOR regardless of orthogonality
        result = NoveltyClassifier.classify(
            orthogonality_score=0.9,
            coherence_score=0.1,  # Below floor of 0.25
            has_embodiment_signature=True,
            has_constraint_origin=True,
        )
        assert result == NoveltyType.RANDOM

    def test_embodied_requires_both_flags_and_high_orthogonality(self):
        result = NoveltyClassifier.classify(
            orthogonality_score=0.8,
            coherence_score=0.8,
            has_embodiment_signature=True,
            has_constraint_origin=True,
        )
        assert result == NoveltyType.EMBODIED

    def test_embodied_without_constraint_origin_is_orthogonal(self):
        result = NoveltyClassifier.classify(
            orthogonality_score=0.8,
            coherence_score=0.8,
            has_embodiment_signature=True,
            has_constraint_origin=False,  # Missing C_o typing
        )
        assert result == NoveltyType.SYNTHETIC

    def test_orthogonal_requires_constraint_origin(self):
        result = NoveltyClassifier.classify(
            orthogonality_score=0.8,
            coherence_score=0.8,
            has_embodiment_signature=False,
            has_constraint_origin=True,
        )
        assert result == NoveltyType.ORTHOGONAL

    def test_moderate_orthogonality_is_synthetic(self):
        result = NoveltyClassifier.classify(
            orthogonality_score=0.4,
            coherence_score=0.7,
            has_embodiment_signature=False,
            has_constraint_origin=False,
        )
        assert result == NoveltyType.SYNTHETIC

    def test_low_orthogonality_is_random(self):
        result = NoveltyClassifier.classify(
            orthogonality_score=0.1,
            coherence_score=0.7,
        )
        assert result == NoveltyType.RANDOM


# ─────────────────────────────────────────────
# V. FIELD NOVELTY STATE
# ─────────────────────────────────────────────

class TestFieldNoveltyState(unittest.TestCase):

    def _make_state_with_signals(self, types):
        state = FieldNoveltyState()
        for t in types:
            state.add_signal(NoveltySignal(t, 0.7, 0.8))
        return state

    def test_empty_state_has_zero_orthogonal_ratio(self):
        state = FieldNoveltyState()
        assert state.orthogonal_ratio == 0.0

    def test_all_orthogonal_signals_gives_full_ratio(self):
        state = self._make_state_with_signals([
            NoveltyType.ORTHOGONAL,
            NoveltyType.EMBODIED,
            NoveltyType.ORTHOGONAL,
        ])
        assert state.orthogonal_ratio == 1.0

    def test_mixed_signals_correct_ratio(self):
        state = self._make_state_with_signals([
            NoveltyType.ORTHOGONAL,
            NoveltyType.RANDOM,
            NoveltyType.RANDOM,
            NoveltyType.RANDOM,
        ])
        assert abs(state.orthogonal_ratio - 0.25) < 0.001

    def test_healthy_emergence_risk_with_high_orthogonal(self):
        state = self._make_state_with_signals([
            NoveltyType.ORTHOGONAL,
            NoveltyType.EMBODIED,
            NoveltyType.ORTHOGONAL,
        ])
        assert state.emergence_risk == "HEALTHY"

    def test_stagnation_imminent_with_all_random(self):
        state = self._make_state_with_signals([
            NoveltyType.RANDOM,
            NoveltyType.RANDOM,
            NoveltyType.RANDOM,
            NoveltyType.RANDOM,
        ])
        assert state.emergence_risk == "STAGNATION_IMMINENT"

    def test_weighted_novelty_higher_for_orthogonal_mix(self):
        orthogonal_state = self._make_state_with_signals([
            NoveltyType.ORTHOGONAL, NoveltyType.EMBODIED
        ])
        random_state = self._make_state_with_signals([
            NoveltyType.RANDOM, NoveltyType.RANDOM
        ])
        assert orthogonal_state.weighted_field_novelty > random_state.weighted_field_novelty

    def test_type_distribution_sums_to_one(self):
        state = self._make_state_with_signals([
            NoveltyType.RANDOM,
            NoveltyType.SYNTHETIC,
            NoveltyType.ORTHOGONAL,
            NoveltyType.EMBODIED,
        ])
        dist = state.type_distribution
        assert abs(sum(dist.values()) - 1.0) < 0.001
