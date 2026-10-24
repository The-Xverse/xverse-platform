---
title: Validation and diagnostics
description: Read validation results and use the Python validation API.
sidebar:
  order: 2
---

Validation checks supplied descriptions against resource structure, references, and admitted Profile semantics. Inputs stay local; the validator does not probe live targets.

## Command results

| Exit status | Meaning | Next action |
| --- | --- | --- |
| 0 | Requested operation succeeded. | Inspect the report or output. |
| 1 | Description or experiment intent was rejected. | Correct the reported input. |
| 2 | Invocation, writing, or internal operation failed. | Check arguments, paths, permissions, and failure details. |

Text diagnostics identify a code, severity, gate, source location when available, pointer, message, and suggested correction. JSON output is better for tooling.

## Use the Python API

```python
from pathlib import Path
from xverse_xdl import validate_files

files = sorted(Path("xdl/examples/v1alpha1").glob("*.xdl.yaml"))
result = validate_files(
    files,
    profile_schema_paths=[
        Path("tests/fixtures/measurement-profile.schema.json")
    ],
)
print(result.is_valid)
for diagnostic in result.diagnostics:
    print(diagnostic.code, diagnostic.message)
```

The [generated Python API](/reference/python/xverse_xdl.html) contains current parameter types and return models.

## Normalize

Normalization produces canonical JSON of resolved descriptions. It can include source mappings for downstream inspection. Canonicalization is not execution and does not prove runtime compatibility.

Use an explicit output path when writing a file. Do not target a source resource or schema path.

## Common problems

- **Missing reference:** supply the referenced resource or repair its identity.
- **Unknown extension:** supply a compatible Profile and its schema.
- **Malformed field:** compare the generated field reference and complete JSON schema.
- **Input size or nesting limit:** inspect the public `LoadLimits` API and the diagnostic rather than disabling bounds blindly.
- **Readiness confusion:** static `Ready` describes declaration completeness, not a running component.

See [generated CLI help](/docs/reference/generated/cli/) for exact current options.
