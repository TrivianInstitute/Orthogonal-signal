# Frozen F027 remediation — 0.2.1

Base: 5563676ad21edf68d8482acc5224dddf6910938d (0.2.0).

EmergenceGuard now validates both the novelty metric and timestamp before classification. NaN, infinities, missing values, booleans and wrong types produce AlertLevel.INVALID with human input required. The original input is retained diagnostically and log formatting tolerates malformed timestamps. No invalid value is silently coerced to NOMINAL. Existing finite threshold boundaries retain their prior results; this does not establish a scientifically healthy human or relational outcome.

API compatibility: consumers matching every AlertLevel must handle INVALID. No persisted-state migration or metric calibration is included. New tests: tests/test_frozen_remediation.py. The original frozen F027 witness is rerun unchanged outside this repository.
