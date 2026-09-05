# Changelog

## [0.2.0] — 2026-09-05

- added an upstream Rosetta 2.0 relational-condition input to human and machine novelty signals;
- qualified effective novelty by RCD without conflating signal coherence and relational condition;
- preserved backward compatibility when no upstream reading is supplied; and
- added collapse, proportionality, and range tests.

The compatibility default is not evidence that an unmeasured field has perfect
relational condition. Research integrations should supply and provenance RCD.
