import unittest
"""
test_governance.py
──────────────────
Trivian Institute — orthogonal-signal repository

Tests for governance layer: emergence_guard.py and conflict_primitive.py.

Core claims under test:
1. EmergenceGuard correctly levels alerts by H_n value
2. Crisis fires below critical bound
3. ConflictPrimitive correctly classifies divergence types
4. Perspectival divergence identified by architectural orthogonality
5. Factional divergence triggers quarantine
6. Emergence potential is higher for perspectival than factional
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orthogonal_signal.governance.emergence_guard import (
    EmergenceGuard,
    AlertLevel,
)
from orthogonal_signal.governance.conflict_primitive import (
    ConflictPrimitive,
    SignalConflict,
    DivergenceType,
    ResolutionPath,
)
from orthogonal_signal.field_constants.novelty_taxonomy import NoveltySignal, NoveltyType
from orthogonal_signal.field_constants.constraint_origin import ConstraintArchitecture


# ─────────────────────────────────────────────
# I. EMERGENCE GUARD
# ─────────────────────────────────────────────

class TestEmergenceGuard(unittest.TestCase):

    def test_healthy_h_n_gives_nominal(self):
        guard = EmergenceGuard()
        alert = guard.evaluate(h_n_value=0.7, timestamp=1.0)
        assert alert.alert_level == AlertLevel.NOMINAL
        assert alert.requires_human_input is False

    def test_declining_h_n_gives_warning(self):
        guard = EmergenceGuard()
        alert = guard.evaluate(h_n_value=0.30, timestamp=1.0)
        assert alert.alert_level == AlertLevel.WARNING

    def test_critical_h_n_requires_human_input(self):
        guard = EmergenceGuard()
        alert = guard.evaluate(h_n_value=0.20, timestamp=1.0)
        assert alert.alert_level == AlertLevel.CRITICAL
        assert alert.requires_human_input is True

    def test_below_lower_bound_gives_crisis(self):
        guard = EmergenceGuard()
        alert = guard.evaluate(h_n_value=0.05, timestamp=1.0)
        assert alert.alert_level == AlertLevel.CRISIS
        assert alert.requires_human_input is True
        assert "CRISIS" in alert.message

    def test_alert_history_accumulates(self):
        guard = EmergenceGuard()
        for i in range(5):
            guard.evaluate(h_n_value=0.5, timestamp=float(i))
        assert len(guard._alert_history) == 5

    def test_current_level_reflects_last_evaluation(self):
        guard = EmergenceGuard()
        guard.evaluate(h_n_value=0.7, timestamp=1.0)
        guard.evaluate(h_n_value=0.05, timestamp=2.0)
        assert guard.current_level == AlertLevel.CRISIS

    def test_alert_levels_escalate_with_declining_h_n(self):
        guard = EmergenceGuard()
        a1 = guard.evaluate(0.7, 1.0)
        a2 = guard.evaluate(0.30, 2.0)
        a3 = guard.evaluate(0.20, 3.0)
        a4 = guard.evaluate(0.05, 4.0)
        levels = [a1.alert_level, a2.alert_level, a3.alert_level, a4.alert_level]
        # Each level should be >= previous (non-decreasing severity)
        for i in range(len(levels) - 1):
            assert levels[i].value <= levels[i+1].value


# ─────────────────────────────────────────────
# II. CONFLICT PRIMITIVE
# ─────────────────────────────────────────────

def make_conflict(
    source_a_type='human',
    source_b_type='language_model',
    semantic_distance=0.5,
):
    """Helper to create a SignalConflict for testing."""
    arch_a = (
        ConstraintArchitecture.human("source_a")
        if source_a_type == 'human'
        else ConstraintArchitecture.language_model("source_a")
    )
    arch_b = (
        ConstraintArchitecture.human("source_b")
        if source_b_type == 'human'
        else ConstraintArchitecture.language_model("source_b")
    )
    signal_a = NoveltySignal(NoveltyType.ORTHOGONAL, 0.8, 0.8)
    signal_b = NoveltySignal(NoveltyType.ORTHOGONAL, 0.7, 0.9)
    conflict = SignalConflict(
        signal_a=signal_a,
        signal_b=signal_b,
        source_a_id="source_a",
        source_b_id="source_b",
        source_a_architecture=arch_a,
        source_b_architecture=arch_b,
        timestamp=1.0,
        system_state_hash="test_hash",
        semantic_distance=semantic_distance,
    )
    return conflict


class TestConflictPrimitive(unittest.TestCase):

    def test_human_machine_moderate_distance_is_perspectival(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict(
            source_a_type='human',
            source_b_type='language_model',
            semantic_distance=0.5,
        )
        divergence = primitive.classify_divergence(conflict)
        assert divergence == DivergenceType.PERSPECTIVAL

    def test_two_humans_high_distance_is_factional(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict(
            source_a_type='human',
            source_b_type='human',
            semantic_distance=0.7,
        )
        divergence = primitive.classify_divergence(conflict)
        assert divergence == DivergenceType.FACTIONAL

    def test_human_machine_very_high_distance_is_contradictory(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict(
            source_a_type='human',
            source_b_type='language_model',
            semantic_distance=0.9,
        )
        divergence = primitive.classify_divergence(conflict)
        assert divergence == DivergenceType.CONTRADICTORY

    def test_perspectival_resolves_to_bifurcation(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict('human', 'language_model', 0.5)
        resolution = primitive.resolve(conflict)
        assert resolution.resolution_path == ResolutionPath.BIFURCATION

    def test_factional_resolves_to_quarantine(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict('human', 'human', 0.7)
        resolution = primitive.resolve(conflict)
        assert resolution.resolution_path == ResolutionPath.QUARANTINE

    def test_perspectival_has_high_emergence_potential(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict('human', 'language_model', 0.5)
        resolution = primitive.resolve(conflict)
        assert resolution.emergence_potential > 0.7

    def test_factional_has_high_factional_risk(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict('human', 'human', 0.7)
        resolution = primitive.resolve(conflict)
        assert resolution.factional_risk > 0.7

    def test_perspectival_requires_dissenter(self):
        primitive = ConflictPrimitive()
        conflict = make_conflict('human', 'language_model', 0.5)
        resolution = primitive.resolve(conflict)
        assert resolution.requires_dissenter is True

    def test_architectural_orthogonality_computed_on_init(self):
        conflict = make_conflict('human', 'language_model', 0.5)
        assert conflict.architectural_orthogonality > 0.0

    def test_same_type_conflict_has_zero_architectural_orthogonality(self):
        conflict = make_conflict('human', 'human', 0.5)
        assert conflict.architectural_orthogonality == 0.0

    def test_batch_resolve_returns_all_resolutions(self):
        primitive = ConflictPrimitive()
        conflicts = [
            make_conflict('human', 'language_model', 0.5),
            make_conflict('human', 'human', 0.7),
            make_conflict('human', 'language_model', 0.9),
        ]
        resolutions = primitive.batch_resolve(conflicts)
        assert len(resolutions) == 3
