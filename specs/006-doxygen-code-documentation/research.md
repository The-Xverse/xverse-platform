# Research: Doxygen Code Documentation

## Decision 1: Python docstrings are the symbol source

**Decision**: Keep documentation next to Python definitions using ordinary docstrings and Doxygen
commands only where parameter, return, or exception detail adds value.

**Rationale**: This keeps IDE help, `help()`, source review, and generated HTML aligned.

**Alternatives considered**: Separate API Markdown would drift; generated docstrings would be hard to review.

## Decision 2: Include all Python trees, enforce production coverage

**Decision**: Doxygen scans `src`, `scripts`, and `tests`. The checker requires docstrings for every
module/class/callable in `src/xverse_xdl` and every module/top-level callable in `scripts`, while test
methods remain executable specifications visible through source browsing.

**Rationale**: This gives full code navigation without burying tests in repetitive prose.

**Alternatives considered**: Excluding tests violates the requested all-code navigation; requiring
docstrings on every test duplicates descriptive test names.

## Decision 3: Treat warnings as validation failures

**Decision**: Capture the Doxygen warning log and fail validation when it is non-empty.

**Rationale**: A successful process exit alone can hide broken references and malformed comments.

**Alternatives considered**: Advisory warnings provide no durable quality gate.

## Decision 4: Keep generated HTML local

**Decision**: Generate under `build/doxygen` and version only inputs.

**Rationale**: Reproducible generated output does not belong in source control and the existing
ignore policy already covers `build/`.

**Alternatives considered**: Committing HTML creates large noisy diffs; hosted publication is not authorized.

