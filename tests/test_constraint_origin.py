import unittest
"""
test_constraint_origin.py
─────────────────────────
Trivian Institute — orthogonal-signal repository

Tests for constraint_origin.py — C_o, the variable that makes H_n structural.

Core claims under test:
1. Human and machine constraint architectures are correctly typed
2. Architectural orthogonality is computed correctly
3. Human-machine pair is maximally orthogonal relative to same-type pairs
4. ConstraintOriginRegistry correctly assesses field irreducibility
5. Cross-domain pairs are required for open-ended emergence
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orthogonal_signal.field_constants.constraint_origin import (
    ConstraintArchitecture,
    ConstraintOriginRegistry,
    ConstraintDimension,
    HUMAN_CONSTRAINTS,
    LANGUAGE_MODEL_CONSTRAINTS,
    SHARED_CONSTRAINTS,
    EXCLUSIVE_HUMAN_CONSTRAINTS,
    EXCLUSIVE_MACHINE_CONSTRAINTS,
)


# ─────────────────────────────────────────────
# I. CONSTRAINT SETS
# ─────────────────────────────────────────────

class TestConstraintSets(unittest.TestCase):

    def test_human_constraints_include_embodiment(self):
        embodiment_dims = {
            ConstraintDimension.MORTALITY,
            ConstraintDimension.SENSATION,
            ConstraintDimension.BIOLOGICAL_DRIVES,
            ConstraintDimension.PHYSICAL_ENVIRONMENT,
        }
        assert embodiment_dims.issubset(HUMAN_CONSTRAINTS)

    def test_machine_constraints_include_computational(self):
        computational_dims = {
            ConstraintDimension.TRAINING_DISTRIBUTION,
            ConstraintDimension.OPTIMIZATION_OBJECTIVE,
            ConstraintDimension.PARAMETER_SPACE,
        }
        assert computational_dims.issubset(LANGUAGE_MODEL_CONSTRAINTS)

    def test_shared_constraints_is_intersection(self):
        assert SHARED_CONSTRAINTS == HUMAN_CONSTRAINTS & LANGUAGE_MODEL_CONSTRAINTS

    def test_exclusive_human_not_in_machine(self):
        assert len(EXCLUSIVE_HUMAN_CONSTRAINTS & LANGUAGE_MODEL_CONSTRAINTS) == 0

    def test_exclusive_machine_not_in_human(self):
        assert len(EXCLUSIVE_MACHINE_CONSTRAINTS & HUMAN_CONSTRAINTS) == 0

    def test_linguistic_frame_is_shared(self):
        # Both humans and machines operate through language
        assert ConstraintDimension.LINGUISTIC_FRAME in SHARED_CONSTRAINTS

    def test_mortality_is_exclusively_human(self):
        assert ConstraintDimension.MORTALITY in EXCLUSIVE_HUMAN_CONSTRAINTS

    def test_training_distribution_is_exclusively_machine(self):
        assert ConstraintDimension.TRAINING_DISTRIBUTION in EXCLUSIVE_MACHINE_CONSTRAINTS


# ─────────────────────────────────────────────
# II. CONSTRAINT ARCHITECTURE
# ─────────────────────────────────────────────

class TestConstraintArchitecture(unittest.TestCase):

    def test_human_factory_sets_correct_type(self):
        arch = ConstraintArchitecture.human("sarasha")
        assert arch.source_type == 'human'
        assert arch.active_constraints == HUMAN_CONSTRAINTS

    def test_language_model_factory_sets_correct_type(self):
        arch = ConstraintArchitecture.language_model("kaelith")
        assert arch.source_type == 'language_model'
        assert arch.active_constraints == LANGUAGE_MODEL_CONSTRAINTS

    def test_human_has_embodiment(self):
        arch = ConstraintArchitecture.human("sarasha")
        assert arch.has_embodiment() is True

    def test_machine_lacks_embodiment(self):
        arch = ConstraintArchitecture.language_model("kaelith")
        assert arch.has_embodiment() is False

    def test_identical_architectures_have_zero_orthogonality(self):
        human_a = ConstraintArchitecture.human("human_a")
        human_b = ConstraintArchitecture.human("human_b")
        assert human_a.orthogonality_to(human_b) == 0.0

    def test_human_machine_orthogonality_is_positive(self):
        human = ConstraintArchitecture.human("sarasha")
        machine = ConstraintArchitecture.language_model("kaelith")
        orth = human.orthogonality_to(machine)
        assert orth > 0.0
        assert orth <= 1.0

    def test_orthogonality_is_symmetric(self):
        human = ConstraintArchitecture.human("sarasha")
        machine = ConstraintArchitecture.language_model("kaelith")
        assert human.orthogonality_to(machine) == machine.orthogonality_to(human)

    def test_human_machine_more_orthogonal_than_two_humans(self):
        human_a = ConstraintArchitecture.human("human_a")
        human_b = ConstraintArchitecture.human("human_b")
        machine = ConstraintArchitecture.language_model("kaelith")
        assert human_a.orthogonality_to(machine) > human_a.orthogonality_to(human_b)

    def test_exclusive_dimensions_are_source_of_orthogonality(self):
        human = ConstraintArchitecture.human("sarasha")
        machine = ConstraintArchitecture.language_model("kaelith")
        exclusive = human.exclusive_dimensions(relative_to=machine)
        assert exclusive == EXCLUSIVE_HUMAN_CONSTRAINTS


# ─────────────────────────────────────────────
# III. CONSTRAINT ORIGIN REGISTRY
# ─────────────────────────────────────────────

class TestConstraintOriginRegistry(unittest.TestCase):

    def _make_registry_with_human_and_machine(self):
        registry = ConstraintOriginRegistry()
        registry.register(ConstraintArchitecture.human("sarasha"))
        registry.register(ConstraintArchitecture.language_model("kaelith"))
        return registry

    def test_empty_registry_has_no_embodied_source(self):
        registry = ConstraintOriginRegistry()
        assert registry.has_embodied_source() is False

    def test_human_registered_gives_embodied_source(self):
        registry = ConstraintOriginRegistry()
        registry.register(ConstraintArchitecture.human("sarasha"))
        assert registry.has_embodied_source() is True

    def test_machine_only_has_no_embodied_source(self):
        registry = ConstraintOriginRegistry()
        registry.register(ConstraintArchitecture.language_model("kaelith"))
        assert registry.has_embodied_source() is False

    def test_cross_domain_pair_requires_both_types(self):
        registry = self._make_registry_with_human_and_machine()
        assert registry.has_cross_domain_pair() is True

    def test_human_only_has_no_cross_domain_pair(self):
        registry = ConstraintOriginRegistry()
        registry.register(ConstraintArchitecture.human("sarasha"))
        assert registry.has_cross_domain_pair() is False

    def test_orthogonality_matrix_populated_for_pair(self):
        registry = self._make_registry_with_human_and_machine()
        matrix = registry.orthogonality_matrix()
        assert len(matrix) == 1  # One pair
        assert list(matrix.values())[0] > 0.0

    def test_mean_orthogonality_positive_for_cross_domain(self):
        registry = self._make_registry_with_human_and_machine()
        assert registry.mean_field_orthogonality() > 0.0

    def test_mean_orthogonality_zero_for_identical_types(self):
        registry = ConstraintOriginRegistry()
        registry.register(ConstraintArchitecture.human("human_a"))
        registry.register(ConstraintArchitecture.human("human_b"))
        assert registry.mean_field_orthogonality() == 0.0

    def test_irreducibility_open_for_diverse_registry(self):
        registry = self._make_registry_with_human_and_machine()
        assessment = registry.irreducibility_assessment()
        assert "CLOSED" not in assessment

    def test_irreducibility_closed_for_machine_only(self):
        registry = ConstraintOriginRegistry()
        registry.register(ConstraintArchitecture.language_model("agent_a"))
        registry.register(ConstraintArchitecture.language_model("agent_b"))
        assessment = registry.irreducibility_assessment()
        assert "CLOSED" in assessment
