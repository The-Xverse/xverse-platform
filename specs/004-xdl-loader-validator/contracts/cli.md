# Command-line contract

Executable: `xdl`

```text
xdl validate [--format text|json] [--profile-schema PATH ...] RESOURCE ...
xdl normalize [--profile-schema PATH ...] [--include-source-map] [-o PATH] RESOURCE ...
xdl version [--format text|json]
```

## Status codes

| Code | Meaning |
|---|---|
| 0 | Requested operation completed with no error diagnostics. |
| 1 | Authored input failed validation; diagnostics were emitted. |
| 2 | Command usage, explicit output write, or internal capability failure. |

## Output

Text diagnostics use one deterministic line per issue followed by the correction. JSON diagnostics
use a versioned report object containing tool version, supported API versions, validity, diagnostics,
and static readiness. `normalize` writes canonical semantic JSON only after gates 1–4 pass. Diagnostics
go to standard error when normalized JSON uses standard output.

An output path is overwritten only when the caller explicitly passes `-o`. Equality with any resource
or Profile-schema input path is rejected. The command performs no telemetry or network request.
