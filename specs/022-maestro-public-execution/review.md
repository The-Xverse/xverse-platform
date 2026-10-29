# Initial read-only consistency review

2026-10-29. Baseline 7fab6a290c3731533c2b88517158055c768b9d4e.
Finding MPX-R01 (BLOCKER for current Studio integration): candidate submission
requires a private runtime object; no admitted public effective-input submission.
Disposition: new separately authorized public capability; old boundary unchanged.
Finding MPX-R02 (MAJOR): Argus plan.semanticDigest identifies the compiled plan,
not Studio input-semantic identity. Disposition: preserve distinct digest fields.
Finding MPX-R03 (MAJOR): Lite flows/Zenoh telemetry cannot establish native X-COM.
Disposition: actual native observation/provider evidence required by AC-07/08.
Finding MPX-R04 (MAJOR): source inspection and generated reviews are not platform
acceptance. Disposition: explicit user acceptance and exact main integration retained.
No implementation, live acceptance or independent review is claimed by this pass.

## Inspection implementation review, pass1 (before repairs)

Candidate: initial public inspection implementation;7 installed-package checks pass.
This is a separate self-review pass, not independent user acceptance.

- MPX-IR01 MAJOR: CanonicalSubmission lacks an explicit resource-selection field.
  Expected plan digest binds the compiled selection, but the written contract also
  requires direct selection agreement. Add public ExperimentSelection and a mismatch
  test; do not silently rely on implicit selection.
- MPX-IR02 MAJOR claim boundary: inspection is static compilation/binding checking,
  not provider effective-configuration or runtime permission admission. Keep T02
  in_progress, executionAllowed false and runtime layers visibly unimplemented.
- MPX-IR03 MINOR: source has no process/writer calls, but tests should explicitly
  fail if compilation inspection dispatches a process or opens an Argus writer.
- MPX-IR04 MINOR: add inspection unit specifications and exact public-boundary
  source/test mapping before extending implementation.
- Packaging observation: force-included Maestro files are copied even for this
  editable install. Initial collection could not see the new module; rebuilt the
  installed package and7 checks passed. Do not validate against stale installed code.

## Effective preparation review, pass2 (before repairs)

13 installed-package checks pass. IR01 explicit selection and IR03 zero-effect
checks are now covered; IR04 unit specifications are present. IR02 remains the
correct stage boundary: no runtime permit or lifecycle dispatcher exists yet.

- MPX-IR05 MINOR: an invalid host provider_id of an unhashable type can produce a
  TypeError instead of the documented stable registration error. Guard its type.
- MPX-IR06 MINOR: a compiler I/O exception can escape the stable public failure
  boundary. Translate it without copying private filesystem diagnostics.
- MPX-IR07 MINOR: the public preparation summary should retain each provider's
  effective source-byte digests separately from the request, not only inside a
  configuration digest. Add the explicit provenance map.
- Residual: independent runtime consumption of the frozen provider configuration
  is not implemented or verified. A provider's source report and static equality
  cannot substitute for actual edited-input execution verification.

- MPX-IR08 MINOR: default dataclass repr can reveal submitted source bytes or
  private provider configuration during debugging. Hide those byte-bearing fields
  from repr and verify the public preparation representation stays metadata-only.


## Inspection/preparation review, pass3

The current installed source matches all inspected implementation modules.18 public-boundary
checks pass, including independent installed CLI identity, edited provider sources,
registration errors, source/config privacy and zero-effect static inspection. IR01,
IR03–IR08 are repaired in this bounded layer. IR02 remains an explicit implementation
boundary: static/effective-source checking does not grant runtime authority. No
independent acceptance, lifecycle execution, native exchange or full goal completion
is claimed. Next work is host runtime permission, phase planning and actual ownership.
