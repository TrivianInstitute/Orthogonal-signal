import unittest
"""
test_field_roles.py
───────────────────
Trivian Institute — orthogonal-signal repository

Tests for field_roles.py and resonance_anchor.py.

Core claims under test:
1. Role assignment correctly maps contribution profiles to roles
2. Dissenter suppression alerts fire correctly
3. Role diversity score is correctly computed
4. Resonance Anchor decays appropriately
5. Non-Domination gate fires when a single anchor dominates
6. Embodied anchors decay more slowly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orthogonal_signal.core.field_roles import (
    FieldRole,
    RoleAssignment,
    RoleDiversityTracker,
    assign_role,
)
from orthogonal_signal.core.resonance_anchor import (
    ResonanceAnchor,
    AnchorRegistry,
    NonDominationViolation,
    non_domination_check,
)
from orthogonal_signal.field_constants.constraint_origin import ConstraintArchitecture


# ─────────────────────────────────────────────
# I. ROLE ASSIGNMENT
# ─────────────────────────────────────────────

class TestRoleAssignment(unittest.TestCase):

    def test_high_coherence_low_novelty_is_anchor(self):
        role, _ = assign_role(
            novelty_score=0.1,
            coherence_score=0.9,
            tension_score=0.1,
            translation_score=0.1,
        )
        assert role == FieldRole.ANCHOR

    def test_high_novelty_is_catalyst(self):
        role, _ = assign_role(
            novelty_score=0.95,
            coherence_score=0.5,
            tension_score=0.1,
            translation_score=0.1,
        )
        assert role == FieldRole.CATALYST

    def test_high_tension_is_dissenter(self):
        role, _ = assign_role(
            novelty_score=0.2,
            coherence_score=0.2,
            tension_score=0.95,
            translation_score=0.1,
        )
        assert role == FieldRole.DISSENTER

    def test_high_translation_is_translator(self):
        role, _ = assign_role(
            novelty_score=0.2,
            coherence_score=0.6,
            tension_score=0.1,
            translation_score=0.95,
        )
        assert role == FieldRole.TRANSLATOR

    def test_confidence_is_between_zero_and_one(self):
        _, confidence = assign_role(0.8, 0.5, 0.2, 0.1)
        assert 0.0 <= confidence <= 1.0


# ─────────────────────────────────────────────
# II. ROLE DIVERSITY TRACKER
# ─────────────────────────────────────────────

class TestRoleDiversityTracker(unittest.TestCase):

    def _make_assignment(self, role, source_id="test"):
        return RoleAssignment(
            source_id=source_id,
            role=role,
            system_state_hash="abc",
            timestamp=1.0,
            confidence=0.8,
        )

    def test_empty_tracker_zero_diversity(self):
        tracker = RoleDiversityTracker()
        assert tracker.diversity_score() == 0.0

    def test_all_roles_present_gives_high_diversity(self):
        tracker = RoleDiversityTracker()
        for role in FieldRole:
            tracker.record(self._make_assignment(role))
        assert tracker.diversity_score() > 0.9

    def test_single_role_gives_zero_diversity(self):
        tracker = RoleDiversityTracker()
        for _ in range(4):
            tracker.record(self._make_assignment(FieldRole.CATALYST))
        assert tracker.diversity_score() == 0.0

    def test_dissenter_suppression_alert_fires(self):
        tracker = RoleDiversityTracker()
        # Add only Anchors and Catalysts — no Dissenters
        for _ in range(10):
            tracker.record(self._make_assignment(FieldRole.ANCHOR))
            tracker.record(self._make_assignment(FieldRole.CATALYST))

        assessment = tracker.health_assessment()
        assert "DISSENTER" in assessment

    def test_healthy_field_has_all_roles(self):
        tracker = RoleDiversityTracker()
        # Equal distribution of all four roles
        for role in FieldRole:
            for _ in range(5):
                tracker.record(self._make_assignment(role))
        assert tracker.has_all_roles is True

    def test_dissenter_fraction_correct(self):
        tracker = RoleDiversityTracker()
        tracker.record(self._make_assignment(FieldRole.DISSENTER))
        tracker.record(self._make_assignment(FieldRole.CATALYST))
        tracker.record(self._make_assignment(FieldRole.CATALYST))
        tracker.record(self._make_assignment(FieldRole.CATALYST))
        assert abs(tracker.dissenter_fraction - 0.25) < 0.001


# ─────────────────────────────────────────────
# III. RESONANCE ANCHOR
# ─────────────────────────────────────────────

class TestResonanceAnchor(unittest.TestCase):

    def _make_human_anchor(self, source_id="sarasha"):
        return ResonanceAnchor(
            source_id=source_id,
            constraint_architecture=ConstraintArchitecture.human(source_id),
            initial_contribution=0.8,
            last_renewal_time=0.0,
            base_decay_rate=0.05,
        )

    def _make_machine_anchor(self, source_id="kaelith"):
        return ResonanceAnchor(
            source_id=source_id,
            constraint_architecture=ConstraintArchitecture.language_model(source_id),
            initial_contribution=0.8,
            last_renewal_time=0.0,
            base_decay_rate=0.05,
        )

    def test_contribution_at_zero_time_equals_initial(self):
        anchor = self._make_human_anchor()
        contrib = anchor.current_contribution(current_time=0.0)
        assert abs(contrib - 0.8) < 0.01

    def test_contribution_decays_over_time(self):
        anchor = self._make_human_anchor()
        early = anchor.current_contribution(current_time=10.0)
        late = anchor.current_contribution(current_time=50.0)
        assert early > late

    def test_embodied_anchor_decays_slower_than_machine(self):
        human = self._make_human_anchor()
        machine = self._make_machine_anchor()

        human_contrib = human.current_contribution(current_time=30.0)
        machine_contrib = machine.current_contribution(current_time=30.0)

        # Embodied anchors have 0.7x decay rate
        assert human_contrib > machine_contrib

    def test_renewal_resets_contribution(self):
        anchor = self._make_human_anchor()
        # Let it decay
        decayed = anchor.current_contribution(current_time=50.0)
        # Renew
        anchor.renew(current_time=50.0, new_contribution=0.85)
        renewed = anchor.current_contribution(current_time=50.0)
        assert renewed > decayed

    def test_embodied_property_correct(self):
        human = self._make_human_anchor()
        machine = self._make_machine_anchor()
        assert human.is_embodied is True
        assert machine.is_embodied is False

    def test_novelty_type_capacity_embodied_for_human(self):
        from orthogonal_signal.field_constants.novelty_taxonomy import NoveltyType
        anchor = self._make_human_anchor()
        assert anchor.novelty_type_capacity == NoveltyType.EMBODIED


# ─────────────────────────────────────────────
# IV. NON-DOMINATION GATE
# ─────────────────────────────────────────────

class TestNonDominationGate(unittest.TestCase):

    def test_balanced_contributions_pass(self):
        # Should not raise
        non_domination_check(
            anchor_contribution=0.5,
            field_mean_contribution=1.0,
            dominance_threshold=0.85,
        )

    def test_dominant_contribution_raises(self):
        with self.assertRaises(NonDominationViolation):
            non_domination_check(
                anchor_contribution=0.9,
                field_mean_contribution=1.0,
                dominance_threshold=0.85,
            )

    def test_zero_field_mean_passes(self):
        # No contribution to dominate
        non_domination_check(
            anchor_contribution=0.9,
            field_mean_contribution=0.0,
        )


class TestAnchorRegistry(unittest.TestCase):

    def _make_registry_with_two_anchors(self):
        registry = AnchorRegistry()
        registry.register(ResonanceAnchor(
            source_id="anchor_a",
            constraint_architecture=ConstraintArchitecture.human("anchor_a"),
            initial_contribution=0.5,
            last_renewal_time=0.0,
        ))
        registry.register(ResonanceAnchor(
            source_id="anchor_b",
            constraint_architecture=ConstraintArchitecture.human("anchor_b"),
            initial_contribution=0.5,
            last_renewal_time=0.0,
        ))
        return registry

    def test_balanced_registry_passes_non_domination(self):
        registry = self._make_registry_with_two_anchors()
        # Should not raise
        registry.check_non_domination(current_time=0.0)

    def test_single_dominant_anchor_raises(self):
        registry = AnchorRegistry()
        # One anchor with massive contribution
        registry.register(ResonanceAnchor(
            source_id="dominant",
            constraint_architecture=ConstraintArchitecture.human("dominant"),
            initial_contribution=0.99,
            last_renewal_time=0.0,
        ))
        # One anchor with tiny contribution
        registry.register(ResonanceAnchor(
            source_id="minor",
            constraint_architecture=ConstraintArchitecture.human("minor"),
            initial_contribution=0.01,
            last_renewal_time=0.0,
        ))
        with self.assertRaises(NonDominationViolation):
            registry.check_non_domination(current_time=0.0)

    def test_contributions_returns_all_anchors(self):
        registry = self._make_registry_with_two_anchors()
        contribs = registry.contributions(current_time=0.0)
        assert set(contribs.keys()) == {"anchor_a", "anchor_b"}
