import math
import pytest
from orthogonal_signal.governance.emergence_guard import EmergenceGuard, AlertLevel

@pytest.mark.parametrize('invalid', [math.nan, math.inf, -math.inf, None, '0.9', {}, [], True])
def test_F027_invalid_input_cannot_clear_crisis(invalid):
    guard = EmergenceGuard(); guard.evaluate(0, 0)
    result = guard.evaluate(invalid, 1)
    assert result.alert_level is AlertLevel.INVALID
    assert result.requires_human_input
    assert guard.current_level is not AlertLevel.NOMINAL
    assert 'INVALID' in guard.alert_log()

@pytest.mark.parametrize('invalid', [math.nan, math.inf, -math.inf, None, 'now'])
def test_F027_invalid_timestamp_withholds_health(invalid):
    guard = EmergenceGuard(); result = guard.evaluate(0.9, invalid)
    assert result.alert_level is AlertLevel.INVALID
    assert 'INVALID' in guard.alert_log()

@pytest.mark.parametrize('metric,level', [(0,AlertLevel.CRISIS),(0.15,AlertLevel.CRISIS),
    (0.25,AlertLevel.CRITICAL),(0.4,AlertLevel.WARNING),(0.400001,AlertLevel.NOMINAL),(1,AlertLevel.NOMINAL)])
def test_F027_valid_boundaries_preserved(metric, level):
    assert EmergenceGuard().evaluate(metric, 0).alert_level is level
