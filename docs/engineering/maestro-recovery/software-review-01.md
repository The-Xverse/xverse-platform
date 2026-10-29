# Read-only software review 01

Candidate: 8abc33e4a55b07188b7fd19403e27711a38750c0.
Review scope: public recovery implementation, receipt provenance/durability,
lifecycle verifier, Start fences and actual read-only retained registration check.
Primary-agent separate review; not independent acceptance. Initial15 and expanded27
recovery checks pass, with actual owned children/Argus. The first exact lifecycle
regression22 passed. An accidentally broad regression directory was interrupted
with134passing cases and no recorded failures; it is not a complete regression pass.
The exact accepted regression selection is still required. The packaged candidate
read the actual retained43-record registration as eligible while preserving failed
writer/incomplete verdicts and all original bytes; no retirement was performed.

## Findings before repair

- MRX-R01 MAJOR: a receipt retains the permit digest but insufficient structured
  grant provenance for an auditor/verifier to validate its original scope, bindings
  and retirement time. Retain the original host grant separately from evidence and
  validate it at the recorded retirement time, preserving current-time expiry rules
  for new writes/retries. Reject altered/unsupported persisted receipt shapes.
- MRX-R02 MAJOR: a retry can return an existing receipt without repeating the root
  durability synchronization after a previous post-link fsync error. Require fsync
  before retry acknowledgement and verify the interrupted publication path. Never
  delete or rewrite the already atomically published immutable receipt.
- MRX-R03 MAJOR: valid Argus envelopes intentionally permit arbitrary namespaced
  extensions. The recovery verifier must additionally enforce the original public
  lifecycle producer/envelope/extension shapes, readiness outcomes and explicit
  terminal failure metadata. Extra unsupported claim fields must fail closed rather
  than be interpreted as the frozen original claim format.
- MRX-R04 MINOR: recovery_status with no configured bindings reports absent, although
  no binding-specific inspection is possible. Report unavailable with binding reason.

Repair each finding in a successor, add targeted adverse checks, repeat affected
and exact accepted regressions, and conduct another read-only review. No candidate
acceptance, original-root retirement, main update or Studio pin change is authorized
by this review. Existing user authorization covers implementation/tests/review;
final platform acceptance remains the user's.
