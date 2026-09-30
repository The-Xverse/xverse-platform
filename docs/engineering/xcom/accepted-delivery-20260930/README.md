# X-COM accepted gateway delivery — portable derived projection (2026-09-30)

This directory contains an explicitly **DERIVED**, portable projection of the sealed original
acceptance, review, inspection, and delivery records for the accepted X-COM gateway baseline. It is
not an original source receipt, and it does not replace or override the immutable originals it
summarizes.

- `projection.json` — machine-readable projection (`schema_version`: 1, `kind`:
  `derived_acceptance_delivery_projection`, `derived`: true).

## What this projection attests

The reviewed candidate `48e85051a419fe1c193afaa47cef40b1e7457fdf` was independently reviewed (T039),
its evidence bundle was terminally inspected (T040), the user explicitly approved it (T041), and it
was delivered to `xverse-platform/main` at that same commit. The `acceptance_attestation_scope` field
is `accepted_gateway_baseline_only`: this projection attests the accepted gateway baseline only.
Approval of a later documentation successor is a separate record and is not covered here.

| Field | Value |
| --- | --- |
| Accepted candidate revision | `48e85051a419fe1c193afaa47cef40b1e7457fdf` |
| Resulting main commit | `48e85051a419fe1c193afaa47cef40b1e7457fdf` |
| Prior main revision | `a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090` |
| User approval | `approved` |
| External tasks | T039 `completed`; T040 `completed`; T041 `accepted_and_delivered` |
| Approval recorded at | `2026-09-30T21:27:41.510394+00:00` |
| Delivered at | `2026-09-30T21:31:16.839972+00:00` |

## Original source references

Each `source_refs` entry records the originating repository, the repository-relative path, and the
frozen SHA-256 of the immutable original. These identities are frozen; the projection neither edits
them nor invents substitute source receipts.

| Key | Repository | Path | SHA-256 |
| --- | --- | --- | --- |
| `approval` | `x-verse_fabric` | `automation/reviews/t041-gateway-repair-acceptance-20260930/approval.json` | `cb055c36b9cd4f730b14accf45d047c51c86d608c1d3cc80dc6195c5c67facdf` |
| `independent_review` | `x-verse_fabric` | `docs/reviews/t039-r6-independent-review-2026-09-30.md` | `edb4e97fe42ba17d961673797690f2d89fa54af9e04c89502aaac1ccfd8150b0` |
| `independent_review_manifest` | `x-verse_fabric` | `automation/reviews/t039-r6-independent-review-20260930/manifest.json` | `cac18b7d78b05fb43cec8228963b189aae5ecebd7d860b130b3ae4113e78ac4f` |
| `terminal_inspection` | `x-verse_fabric` | `docs/reviews/t040-r6-terminal-inspection-2026-09-30.md` | `9ef2354c7f6c4d6cea1b15a89446cc8c858a838eb9ef278dbcbfc31d59f8900b` |
| `terminal_inspection_manifest` | `x-verse_fabric` | `automation/reviews/t040-r6-terminal-inspection-20260930/manifest.json` | `0db9a2d68e2b54eccb464bdbf5b7a17b8aa21f36845d9cc9cafb1caa349fa25c` |
| `delivery` | `x-verse_fabric` | `automation/reviews/t041-gateway-repair-acceptance-20260930/delivery/delivery.json` | `9db6ea5cc1f217c0e3ab4d9b30a0fc41a5b2e2b0d4c39e9f29147b4849c9b2c7` |
| `delivery_report` | `x-verse_fabric` | `docs/reviews/t041-gateway-repair-delivery-2026-09-30.md` | `08c864440bac385ad7b9a551f113bdf6c33be172914d127bc88e5688b6c38022` |
| `delivery_manifest` | `x-verse_fabric` | `automation/reviews/t041-gateway-repair-acceptance-20260930/manifest.json` | `095b9d3fe1e990cc50433f762444c9b453941b15d55701ad5402bf90b4d74e4e` |

## Retained limitations

The projection retains the accepted baseline's important limitations accurately:

- The gateway watch association is a logical, single-matching-watch lifecycle association, not OS
  process peer authentication or an authorization primitive.
- Shutdown requests gRPC shutdown with a 100 ms grace deadline before forced cancellation; that
  deadline does not preempt or bound an executing RPC callback, so destructor completion still
  requires those callbacks to return. No fixed total-destruction bound is claimed.
- The reported lease identity is volatile, in-memory, session-scoped state and is not persisted;
  durable recorded stimulation outcomes are reconciled separately from the lease identity, and an
  absent durable stimulation intent leaves the outcome unknown and does not authorize an implicit
  retry.
- Sanitizer coverage is complete for the owned production translation units, with the admitted
  prebuilt gRPC dependency retaining its documented `GRPC_ASAN_SUPPRESSED` and ABI-size
  qualification; the third-party gRPC dependency is not claimed to be sanitized.
- `T037-OPEN-06` remains open: the global Python docstring coverage limitation is retained, and no
  global `--self-test --coverage-only` result is claimed as passing.
- Conformance retains the admitted qualified predecessor replay (26 inspections); it is not a
  universal predecessor-conformance claim.
- The T036 evidence is a measured in-process owned-loopback disabled/enabled-tap benchmark with the
  reported non-production scope; the enabled-tap case is recorded as an observation and is not
  gated, and no general production performance, transport, or timing guarantee is inferred.

## Boundaries

This projection makes no production-readiness, deployed-service, legacy-compatibility, parity, or
certification claim. It contains no host-specific absolute path, credential, private source excerpt,
or sensitive deployment detail. The documentation/evidence reconciliation that produced this
projection is itself a separate successor candidate and still requires its own review and explicit
acceptance before it is accepted or merged.
