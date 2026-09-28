# T017 Detailed Design — Profile v0.1 Schema, Activation-Plan v1 Schema, Digest/Provenance, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T017 |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `a78d6d55dd5a68b1572cf5a594100dfba3be523e` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Governing ADRs | ADR-0016, ADR-0018, ADR-0020 |
| Language / tooling | JSON Schema Draft 2020-12; Python 3.11+ for `scripts/validate_xcom_plan.py` and the pytest validation modules (no X-COM runtime, no C++) |

This design is written **before** implementation. The implementation must realise every named unit and rule.
The identifiers below are fixed by this document; the schemas' member names are the interface T018/T019
consume.

## 2. Fixed identifiers and vocabularies

### 2.1 Artifact identifiers

| Identifier | Path |
| --- | --- |
| `PROFILE_SCHEMA` | `xdl/profiles/xcom-v0.1.schema.json` |
| `PLAN_SCHEMA` | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` |
| `PROFILE_CONTRACT` | `specs/007-xcom-core/contracts/xdl-profile.md` |
| `PLAN_VALIDATOR` | `scripts/validate_xcom_plan.py` |
| `PLAN_TESTS` | `tests/xcom/activation_plan/` |
| `PLAN_FIXTURES` | `tests/xcom/activation_plan/fixtures/` |
| `PLAN_DOCS` | `docs/engineering/xcom/t017/` |

### 2.2 Closed vocabularies

- **Profile `kind`** (exactly five): `interface-policy`, `flow-policy`, `network-provider`,
  `observation-policy`, `validation-policy`.
- **Profile `schemaVersion`**: const `"0.1"`.
- **Plan `planVersion`**: const `"1"`.
- **Plan `status`**: `inspectable`, `activatable`.
- **Interaction kind** (used inside `interface-policy`): `signal`, `message`, `service`.
- **Overflow policy** (used inside `flow-policy`): `drop-oldest`, `drop-newest`, `coalesce`,
  `lossless-backpressure`, `reject`, `fail-closed`.
- **Payload access** (used inside `observation-policy`): `metadata-only`, `allow-listed`.
- **Digest algorithm**: `sha256`, value pattern `^[0-9a-f]{64}$`.
- **Input-resolution state**: `resolved`, `unresolved`.
- **Diagnostic severity**: `error`, `warning`, `info`.

## 3. `PROFILE_SCHEMA` — `io.xverse.xcom` Profile v0.1 (`T017-U-01`)

### 3.1 Top level

A closed object with required members:

| Member | Type | Rule |
| --- | --- | --- |
| `schemaVersion` | string | const `"0.1"` |
| `kind` | string | enum of the five Profile kinds |
| `target` | object | the decorated logical identity (closed): `apiVersion` (const `"xverse.io/xdl/v1alpha1"`), `kind` (enum `Component`,`Deployment`,`Scenario`), `namespace`, `name`, optional `version` |
| `policy` | object | discriminated by `kind` via `allOf` conditional subschemas |

`additionalProperties: false`; a duplicate/conflicting policy (two payloads for the same decorated identity) is
rejected by the caller/validator, not by a single document instance.

### 3.2 Per-kind `policy` forms (each closed)

| `kind` | Required `policy` members | Notes |
| --- | --- | --- |
| `interface-policy` | `interactionKind` (enum), `schemaId`, `schemaVersion`, `encoding`, `semanticCompatibility` | binds one logical interface's schema/encoding contract |
| `flow-policy` | `ordering`, `reliability`, `deadlineMs`, `retry`, `queueDepth`, `overflow`, `observationPoints` | `overflow` enum from §2.2; `retry` integer ≥ 0 |
| `network-provider` | `requiredCapabilities` (unique array), `fidelity`, `limitations` (unique array) | declares provider requirements and declared fidelity; no address |
| `observation-policy` | `filters`, `payloadAccess` (enum), `bounds`, `validityEffect` | `bounds` finite; metadata-only default |
| `validation-policy` | `allowedActions` (unique array), `injectionPoints`, `serviceEmulation`, `timePolicy`, `quotas`, `permitPolicyRef` | `serviceEmulation` requires an explicit `permitPolicyRef` |

### 3.3 Placement and safety rules (`PROFILE_CONTRACT` addition, `T017-U-04`)

- The payload is legal only at an XDL `extensions["io.xverse.xcom"]` member of a `Component`, `Deployment`,
  or `Scenario` resource (or as the payload selected by a Profile resource's `spec.schemaRef`).
- No member may carry a provider address, credential, validation permit, live handle, or tool session.
  Environment realization stays on Deployment network/binding extensions; scenario validation policy stays on
  Scenario extensions.
- Unknown fields and unsupported versions fail closed.

## 4. `PLAN_SCHEMA` — canonical activation-plan v1 (`T017-U-02`)

### 4.1 Top level (closed, all required)

| Member | Represents (`contracts/communication-plan.md`) | Shape |
| --- | --- | --- |
| `planVersion` | plan format version | const `"1"` |
| `digest` | canonical digest | `{algorithm:"sha256", value:^[0-9a-f]{64}$}` |
| `generator` | generator version | `{task, version}` |
| `provenance` | source identities, API versions, source digests, graph digest, generation time | see §4.2 |
| `contracts` | communication contracts and schema/version references | ordered array keyed by `contractId` |
| `endpoints` | endpoint roles | ordered array keyed by `endpointId` |
| `routes` | route graph | ordered array keyed by `routeId` |
| `providers` | selected provider IDs and capability requirements | ordered array keyed by `providerId` |
| `policies` | queue/ordering/reliability/deadline/retry/overflow/backpressure | object, closed |
| `observationPoints` | allowed observation points and payload policies | ordered array keyed by `tapId` |
| `stimulation` | allowed stimulation actions and permit-policy references | object, closed (`actions`, `permitPolicyRefs`) |
| `clockDomains` | clock domains | ordered array keyed by `clockDomainId` |
| `activationOrder` | activation order | ordered array of route/endpoint ids |
| `diagnostics` | deterministic diagnostics | ordered array keyed by `(code, targetId)` |
| `status` | inspectable vs activatable | enum |
| `inputResolution` | unresolved identity/schema/capability/time/ownership/policy input | object with the six named states from §2.2 |

### 4.2 `provenance` (closed, all required)

| Member | Shape |
| --- | --- |
| `generatedAt` | string, `format: date-time` |
| `graphDigest` | `{algorithm:"sha256", value:^[0-9a-f]{64}$}` |
| `resources` | ordered array keyed by `(apiVersion, kind, namespace, name, version?)`; each entry `{apiVersion, kind, namespace, name, version?, sourceDigest}` |

### 4.3 Inspectable-versus-activatable rule (`T017-SR-005`)

The schema carries a conditional constraint:

- `status = "activatable"` ⇒ every member of `inputResolution` equals `"resolved"`;
- `status = "inspectable"` is always permitted when the document is otherwise well formed.

A plan that claims `activatable` while any input is `unresolved` is rejected. This models
`contracts/communication-plan.md` "inspectable but cannot activate".

### 4.4 Deterministic ordering and uniqueness (`T017-SR-006`)

Every identity-bearing array is ordered by its declared key and carries unique keys; `activationOrder` is a
permutation of declared route/endpoint ids with no duplicates; `diagnostics` is ordered by `(code, targetId)`.
The validator enforces ordering and uniqueness; the schema enforces uniqueness with `uniqueItems` and the
declared key patterns.

## 5. Canonical serialization and digest/provenance contract (`T017-U-03`)

### 5.1 Canonical serialization

The canonical byte string of a plan is the UTF-8 encoding of its JSON value with:

1. object members ordered lexicographically by member name (Unicode code-point order);
2. no insignificant whitespace (`separators=(",", ":")`);
3. every number whose value is mathematically integral emitted in its single integer form — a JSON token
   such as `100.0` serialises as `100`, so `100` and `100.0` produce byte-identical canonical bytes and the
   same digest; non-finite numbers rejected;
4. arrays in their validated order (already deterministic per §4.4);
5. no duplicate object members: a document that repeats a member name is rejected fail-closed before
   canonicalization rather than collapsed last-wins.

T019 must reproduce rules 1–5 independently in C++ (including the integral-number normalization of rule 3)
so the two implementations agree on the digest for any accepted plan body.

### 5.2 Digest

- **Digested region**: the plan value with the top-level `digest` member removed.
- **Domain separator**: the ASCII byte prefix `xverse.xcom.activation-plan.v1` followed by one `0x00` byte,
  concatenated with the canonical bytes.
- **Algorithm**: SHA-256; the `digest` member is `{"algorithm":"sha256","value":"<64 lowercase hex>"}`.
- **Independence**: T019 recomputes the digest over the received plan body and rejects a mismatch
  (`data-model.md` invariant 7). T017 supplies the reference recomputation in the validator and the digest
  vectors.

### 5.3 Reproducibility

`provenance.generatedAt` participates in the digested region. The compiler (T018) must obtain it from an
explicit deterministic input; when no input is supplied it uses the fixed sentinel `1970-01-01T00:00:00Z`.
Therefore semantically equivalent normalized inputs produce byte-identical canonical bytes and the same
digest (SC-002). T017 defines and checks this with vectors; T018/T019/T020 prove it end to end.

### 5.4 `PROFILE_CONTRACT` addition (`T017-U-04`)

Append two sections to `specs/007-xcom-core/contracts/xdl-profile.md`:

1. **"Profile v0.1 payload grammar"** — §3.1–§3.3 of this design.
2. **"Activation-plan v1 digest and provenance"** — §5.1–§5.3 of this design.

No existing sentence in the file is changed.

## 6. `PLAN_VALIDATOR` — offline deterministic checker (`T017-U-05`)

### 6.1 CLI

| Invocation | Behaviour |
| --- | --- |
| `--verify` | Parse both schemas, assert valid Draft 2020-12 and closed-ness, assert discriminator/coverage/ordering/digest rules, and validate the bounded fixtures; exit 0 on success |
| `--self-test` | Run the controlled positive fixture and every declared negative case, asserting each declared exit class with no partial success |
| `--check-human` | Recompute the human-readable summary and assert it matches the committed expectation (determinism/consistency check) |

### 6.2 Exit classes (distinct per failure family)

| Exit | Class | Meaning |
| --- | --- | --- |
| 0 | `OK` | all checks pass |
| 2 | `SCHEMA_INVALID` | a schema is not valid Draft 2020-12, not closed, or violates a structural rule |
| 3 | `PROFILE_INVALID` | a Profile payload violates discriminator/grammar/placement/safety rules |
| 4 | `PLAN_INVALID` | a plan violates required-content/ordering/uniqueness/inspectable rules |
| 5 | `DIGEST_INVALID` | canonical serialization or digest/provenance rule violated |
| 6 | `IO_ERROR` | unreadable/missing/over-bound input, or an unavailable dependency |
| 7 | `BOUNDARY_INVALID` | a candidate changed an unauthorized path or promoted a REF-002 target |

### 6.3 Rules checked

- `PROFILE_SCHEMA` and `PLAN_SCHEMA` are valid Draft 2020-12 and `additionalProperties: false` at every
  object; `kind` enum is exactly the five forms; `planVersion` is const `"1"`.
- Every required-content group of `communication-plan.md` maps to a required plan member (§4.1).
- Ordering/uniqueness of every identity-bearing array.
- The inspectable/activatable conditional rule.
- Recompute the digest per §5 and compare against the recorded value for every positive fixture.
- Reject a document with a duplicate object member, and emit every mathematically integral number in its
  single integer form (§5.1), so equivalent integral representations share one digest.
- Apply the declared input bounds to every parsed document: schemas and fixtures with the per-fixture 1 MiB
  bound, a supplied document with the 5 MiB bound, and the depth, node, and wall-clock bounds fail-closed.
- Check the authorized-path boundary only against a caller-supplied candidate changed-path set
  (`--verify --changed-paths <file>`); the offline validator starts no child process, so the deterministic
  gate performs the same boundary check externally with `git diff --name-only`.
- Read the authoritative REF-002 disposition record and reject any direct communication target recorded as
  promoted rather than `allocated`/`deferred` `architectural-target`.
- No schema or fixture contains a domain primitive, credential, private address, or absolute host path.
- Offline: imports limited to stdlib (`json`, `hashlib`, `re`, `pathlib`) and `jsonschema`/`referencing`
  (the repository's declared schema dependencies); no network, subprocess, or filesystem write.

## 7. `PLAN_TESTS` and `PLAN_FIXTURES` (`T017-U-06`, `T017-U-07`)

Three pytest modules under `tests/xcom/activation_plan/`:

| Module | Covers |
| --- | --- |
| `test_profile_schema.py` | `T017-SR-001..003`: valid payload accepted; each `NEG-Pxx` rejected |
| `test_activation_plan_schema.py` | `T017-SR-004..006`: valid plan accepted; each `NEG-Axx` rejected; inspectable accepted |
| `test_digest_contract.py` | `T017-SR-007`: canonical byte-stability, domain separation, digest round-trip, and drift detection (`NEG-D01..D04`) |

Fixtures are small (≤ 1 MiB), public-safe JSON files under `tests/xcom/activation_plan/fixtures/`. Tests
import the validator's pure functions and/or invoke `--verify`/`--self-test`; they perform no network,
subprocess, or filesystem write.

## 8. Failure semantics

| T017 condition | Outcome |
| --- | --- |
| unknown field, unknown `kind`, unsupported version | `rejected` (fail closed) |
| missing required member or required content group | `rejected` |
| duplicate identifier or out-of-order collection | `rejected` |
| `activatable` with any unresolved input | `rejected` |
| digest mismatch or malformed digest | `rejected` |
| canonical serialization non-deterministic | `failed` (defect, not a data error) |
| over-bound input, unreadable dependency | `failed` (IO class) |
| candidate change outside authorized paths / REF-002 promotion | `failed` (boundary class) |

No unknown outcome is reported as success; the validator never emits a passing result for a partial check.

## 9. Cross-language contract at the boundary

The plan schema and digest rule are the **only** interface between the Python compiler (T018) and the C++
decoder (T019). T017 fixes:

- the JSON member names, types, and closed vocabularies (schema);
- the canonical serialization rule and the domain-separated SHA-256 digest;
- the fail-closed rules and the inspectable/activatable distinction.

T019 must reproduce the same rules independently in C++ (`nlohmann/json`, bounded decode) and reject a
version/digest/capability mismatch. T017 does not implement that decoder.

## 10. Unit and artifact trace

| Requirement | Design unit | Artifact | Design section |
| --- | --- | --- | --- |
| T017-SR-001 | `T017-U-01`, `T017-U-04` | `PROFILE_SCHEMA`, `PROFILE_CONTRACT` | §3.1 |
| T017-SR-002 | `T017-U-01` | `PROFILE_SCHEMA` | §3.2 |
| T017-SR-003 | `T017-U-01`, `T017-U-04` | `PROFILE_SCHEMA`, `PROFILE_CONTRACT` | §3.3 |
| T017-SR-004 | `T017-U-02` | `PLAN_SCHEMA` | §4.1, §4.2 |
| T017-SR-005 | `T017-U-02`, `T017-U-05` | `PLAN_SCHEMA`, `PLAN_VALIDATOR` | §4.3, §6.3 |
| T017-SR-006 | `T017-U-02`, `T017-U-05` | `PLAN_SCHEMA`, `PLAN_VALIDATOR` | §4.4, §6.3 |
| T017-SR-007 | `T017-U-02`, `T017-U-03`, `T017-U-05` | `PLAN_SCHEMA`, `PROFILE_CONTRACT`, `PLAN_VALIDATOR` | §4.2, §5, §6.3 |
| T017-SR-008 | `T017-U-05` | `PLAN_VALIDATOR` | §6 |
| T017-SR-009 | `T017-U-06`, `T017-U-07` | `PLAN_TESTS`, `PLAN_FIXTURES` | §7 |
| T017-SR-010 | `T017-U-04` | `PROFILE_CONTRACT` | §3.3, §5.4 |
| T017-SR-011 | `T017-U-04`, `T017-U-05`, `T017-U-08` | `PROFILE_CONTRACT`, `PLAN_VALIDATOR`, `PLAN_DOCS` | §6.2, §8 |
