# Clarifications: Doxygen Code Documentation

**Date**: 2026-09-20

No blocking clarification question remained after applying the user's explicit scope and the
repository constitution.

## Recorded decisions

1. "All code" covers Python files in `src/`, `scripts/`, and `tests/`; strict symbol docstring
   coverage applies to production package code and reusable scripts.
2. Generated HTML is a local build artifact and remains ignored; its inputs are versioned.
3. Documentation changes may clarify contracts but may not change behavior or public signatures.
4. The generated main page must repeat the prototype maturity and legacy-execution boundary.

