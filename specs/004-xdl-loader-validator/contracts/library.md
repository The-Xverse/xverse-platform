# Library contract

Package: `xverse_xdl`

## Stable initial surface

```python
from xverse_xdl import (
    LoadLimits,
    ResourceIdentity,
    Diagnostic,
    NormalizedResource,
    ValidationResult,
    validate_files,
    validate_sources,
    canonical_json,
)
```

`validate_files(paths, *, profile_schema_paths=(), limits=LoadLimits()) -> ValidationResult`
reads only the named paths. `validate_sources(sources, *, profile_schema_paths=(), limits=...)` accepts
resource inputs as in-memory `(name, bytes)` pairs while Profile schemas remain explicit local file
paths. Neither function raises for authored-data errors; they return diagnostics. Programmer misuse
and impossible internal states may raise documented Python exceptions.

`canonical_json(result_or_resource, *, include_source_map=False) -> str` returns UTF-8-compatible JSON
text with stable ordering and one trailing newline. It never serializes live parser or schema objects.

## Compatibility

The package version is independent of `xverse.io/xdl/v1alpha1`. The module exposes
`SUPPORTED_API_VERSIONS`. New package patch/minor releases may improve diagnostics without changing
accepted semantics. Any change to accepted XDL meaning requires the language API-version process.

## Immutability

Public dataclasses are frozen. Collections are tuples or read-only mappings. Returned semantic data
is recursively frozen; callers cannot mutate a result and thereby alter another validation outcome.
