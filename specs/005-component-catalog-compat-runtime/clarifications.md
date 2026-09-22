# Clarification record: Component catalog and compatibility runtime

**Date**: 2026-09-20
**Method**: Spec Kit ambiguity scan against M0 findings, M2 XDL contracts, capability 004 approval,
and architecture guidance section 38.

| ID | Area | Decision | Effect |
|---|---|---|---|
| C01 | Current authorization | Produce M3 specification/design only. | No code, adapter, target selection, or legacy execution in this delivery. |
| C02 | Catalog language | Derive entries from exact Deployment binding → System component instance → Component relationships; place typed runtime data only in `io.xverse.runtime.compatibility` on the binding. | No authored catalog document, second language, new kind, or logical-resource realization leakage. |
| C03 | Discovery | Use an explicit local catalog input set only. | No repository scanning, registry lookup, ambient path lookup, or network discovery. |
| C04 | Lifecycle ownership | The compatibility runtime owns only resources it creates or receives through an approved provider action. | Broad legacy cleanup, process-name killing, and inferred remediation are prohibited. |
| C05 | Readiness | Readiness requires declared observable evidence; sleeps are timing constraints only. | Prevents source-observed fixed delays from becoming a health contract. |
| C06 | Execution gate | Catalog derivation and planning are side-effect-free; execution needs a target-specific permit. | M3 design does not authorize running a legacy component. |
| C07 | First proof | Use a controlled fixture before a separately approved legacy component. | Fixture success is not legacy compatibility or parity evidence. |
| C08 | Baseline selection | Preserve both M0 cruise-control paths as alternatives and select neither. | R01 remains unresolved until a later owner-supported target/environment decision. |
| C09 | Sensitive detail | Public catalog projections and evidence use indirect non-secret references and explicit withheld markers. | No credentials, unresolved secret dependencies, private infrastructure, sensitive paths, or proprietary payloads enter repository content. |
| C10 | Repository direction | Platform owns catalog/runtime abstractions; a future component-specific adapter belongs in xverse-compat. | This platform specification tracks companion work without duplicating it. |
| C11 | Planning/permit | Planning is permit-free and side-effect-free; execution requires a matching unexpired single-use permit. | Plans remain reviewable without creating execution authority. |
| C12 | Permit trust | The permit is an operational approval record; host permissions remain access control. | M3 makes no authentication, signature, or identity-provider claim. |
| C13 | Ownership | Only provider-issued handles bound to an execution/action establish ownership. | Names, ports, paths, and ambient discovery cannot authorize stop or cleanup. |
| C14 | Lifecycle recovery | Starts/stops are idempotent, concurrent mutation is serialized/rejected, and restart requires handle reconciliation. | Prevents duplicates and post-crash mutation of unverified resources. |
| C15 | Evidence failure | Persist intent before mutation; outcome failure blocks new starts but permits owned observe/stop/cleanup. | Safety cleanup remains possible while evidence is classified incomplete. |
| C16 | Secrets | M3 neither resolves nor injects secrets. | Secret-dependent entries are visible but blocked before planning/execution. |
| C17 | Incomplete candidate plans | Runtime Profile v0.2 may declare stable `XVERSE-PLAN-*` blocker codes for evidence gaps that do not make the XDL graph structurally invalid. | A nominated candidate remains catalog-visible and yields a deterministic, inspectable blocked plan; declared blockers never waive schema validation or authorize execution. |
| C18 | Supplemental references | Architecture requirements and reported integrations may inform the closure checklist but cannot supply owner approval, immutable environment identity, verified interface behavior, or live readiness evidence. Conflicting startup sequences remain unresolved. | REF-001/REF-002 do not close a plan blocker or select gateway/S-CORE ordering; the closure packet requires direct evidence for each decision. |
| C19 | Static interface evidence | Revision-pinned source/configuration inspection may narrow a target contract but cannot establish peer interoperability, live readiness, graceful shutdown, or owner acceptance. | Record route counts, transformations, versions, and hazards as observed limits; retain all affected blockers until approved runtime evidence exists. |

No unresolved clarification remains. M0 findings R01–R05, completion of the selected-component
decision, execution permit, adapter implementation, and runtime execution remain future gates.
