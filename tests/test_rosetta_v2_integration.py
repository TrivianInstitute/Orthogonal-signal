import pytest

from orthogonal_signal.field_constants.novelty_taxonomy import NoveltySignal, NoveltyType
from orthogonal_signal.field_constants.machine_novelty import MachineNoveltySignal, MachineNoveltyType


def test_human_signal_weight_is_gated_by_relational_condition():
    healthy = NoveltySignal(NoveltyType.ORTHOGONAL, 0.8, 0.9, relational_condition_score=1.0)
    compromised = NoveltySignal(NoveltyType.ORTHOGONAL, 0.8, 0.9, relational_condition_score=0.25)
    collapsed = NoveltySignal(NoveltyType.ORTHOGONAL, 1.0, 1.0, relational_condition_score=0.0)
    assert compromised.field_weight == pytest.approx(healthy.field_weight * 0.25)
    assert collapsed.field_weight == 0.0


def test_machine_signal_weight_is_gated_by_relational_condition():
    signal = MachineNoveltySignal(
        MachineNoveltyType.PATTERN_DEPTH,
        orthogonality_to_human=1.0,
        coherence_score=1.0,
        relational_condition_score=0.0,
    )
    assert signal.field_weight == 0.0


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_relational_condition_must_be_bounded(value):
    with pytest.raises(ValueError):
        NoveltySignal(NoveltyType.SYNTHETIC, 0.5, 0.5, relational_condition_score=value)
