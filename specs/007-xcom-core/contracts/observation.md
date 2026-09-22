# Contract: X-COM observation boundary

An observation tap attaches to a declared logical route point using an exact filter and payload policy.
The core emits immutable normalized records to a bounded observer sink.

## Modes

- `metadata-only`: no payload bytes are exposed;
- `controlled-payload`: exposes only the declared payload view and reports redaction/truncation/decode
  state;
- `lossless-validation`: observation backpressure may affect the route only because the experiment
  explicitly includes that behavior.

Best-effort observer failure, delay, or disconnection cannot block or reorder the normal route. Queue
overflow follows the configured drop or coalesce rule and increments deterministic counters. A test
result that loses required records is marked degraded or invalid according to its declared criterion.

Observation records include route and logical identities, origin, schema identity, source/observation
time and clock domains, sequence/correlation/causation, sizes, outcome, payload-view status, and tap
counters. Export to Argus, OpenTelemetry, files, or dashboards requires a separate adapter.

