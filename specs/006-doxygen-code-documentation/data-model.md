# Data Model: Doxygen Code Documentation

This documentation-only capability introduces no runtime data model.

## Documentation source

- **Path**: repository-relative source path.
- **Kind**: package module, support script, test source, or authored page.
- **Symbols**: classes, functions, methods, attributes, and source locations extracted by Doxygen.
- **Narrative**: purpose, parameters, results, failure behavior, maturity, and boundaries.

## Validation result

- **Coverage errors**: missing docstrings with path, line, and qualified symbol.
- **Doxygen result**: process status and warning log.
- **Output evidence**: existence of `build/doxygen/html/index.html`.
- **State**: valid only when all three checks pass.

