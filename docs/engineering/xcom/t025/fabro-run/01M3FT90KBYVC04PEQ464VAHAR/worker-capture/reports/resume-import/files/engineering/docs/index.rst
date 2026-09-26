Engineering traceability
========================

Generated from canonical engineering JSON records.

.. test:: Integration.IndependentControllerScopes passes: consumption and lifecycle bookkeeping stay isolated 
   :id: NEED_T025_M_I_CONTROLLER

   Canonical ID: ``T025-M-I-CONTROLLER``; revision: ``1``.

   Integration.IndependentControllerScopes passes: consumption and lifecycle bookkeeping stay isolated across controller scopes.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "d952d0deee23b49457630521705dc918336980300802ef322aa18f8ceeed8e88"}``.

.. test:: Integration.MappedValidityCrossDomainLifecycle passes: a permit validity interval expressed in anoth
   :id: NEED_T025_M_I_CROSSDOMAIN

   Canonical ID: ``T025-M-I-CROSSDOMAIN``; revision: ``1``.

   Integration.MappedValidityCrossDomainLifecycle passes: a permit validity interval expressed in another domain is resolved only through a declared mapping and drives the lifecycle.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "d952d0deee23b49457630521705dc918336980300802ef322aa18f8ceeed8e88"}``.

.. test:: Integration.GenerationRotationInvalidatesLiveHandle passes: advancing a controller generation invali
   :id: NEED_T025_M_I_GENERATION

   Canonical ID: ``T025-M-I-GENERATION``; revision: ``1``.

   Integration.GenerationRotationInvalidatesLiveHandle passes: advancing a controller generation invalidates previously issued handles without perturbing other sessions.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "d952d0deee23b49457630521705dc918336980300802ef322aa18f8ceeed8e88"}``.

.. test:: Integration.QuotaExhaustionThroughTransitionPath passes: quota exhaustion through the transition pat
   :id: NEED_T025_M_I_QUOTA

   Canonical ID: ``T025-M-I-QUOTA``; revision: ``1``.

   Integration.QuotaExhaustionThroughTransitionPath passes: quota exhaustion through the transition path is explicit and non-mutating.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "d952d0deee23b49457630521705dc918336980300802ef322aa18f8ceeed8e88"}``.

.. test:: clang-tidy reports no diagnostic over the eight enabled rules (bugprone-branch-clone, cppcoreguideli
   :id: NEED_T025_M_SA_CLANGTIDY

   Canonical ID: ``T025-M-SA-CLANGTIDY``; revision: ``1``.

   clang-tidy reports no diagnostic over the eight enabled rules (bugprone-branch-clone, cppcoreguidelines-pro-type-member-init, cppcoreguidelines-special-member-functions, misc-const-correctness, modernize-use-nodiscard, performance-unnecessary-copy-initialization, performance-unnecessary-value-param, readability-make-member-function-const).

   Source: ``{"path": "src/xverse/xcom/src/validation_session.cpp", "sha256": "ac6b70183cfd1c3d00efdcaddaeadf9eb14cc55334a5dd9a3fa3719b681daa71"}``.

.. test:: Compile-time static_asserts hold: non-copyability/non-movability of TimeAuthority, PermitRegistry, a
   :id: NEED_T025_M_SA_COMPILE

   Canonical ID: ``T025-M-SA-COMPILE``; revision: ``1``.

   Compile-time static_asserts hold: non-copyability/non-movability of TimeAuthority, PermitRegistry, and SessionManager; the exhaustive constexpr transition table; permit immutability; diagnostic payload-freedom and size bound.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "ec0bc335fcfdef485c0b89f6934b4c1778853c1194a0845f21011fa88b8384c5"}``.

.. test:: gcovr reports line coverage over the current library source for the passing unit/integration/validat
   :id: NEED_T025_M_SA_COVERAGE

   Canonical ID: ``T025-M-SA-COVERAGE``; revision: ``1``.

   gcovr reports line coverage over the current library source for the passing unit/integration/validation suites (92.0% of 800 lines; recorded in engineering/quality-evidence.json).

   Source: ``{"path": "src/xverse/xcom/src/validation_session.cpp", "sha256": "ac6b70183cfd1c3d00efdcaddaeadf9eb14cc55334a5dd9a3fa3719b681daa71"}``.

.. test:: Doxygen builds with WARN_AS_ERROR=YES over the public API with zero audit issues and a per-symbol un
   :id: NEED_T025_M_SA_DOXYGEN

   Canonical ID: ``T025-M-SA-DOXYGEN``; revision: ``1``.

   Doxygen builds with WARN_AS_ERROR=YES over the public API with zero audit issues and a per-symbol unit-specification link.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "ec0bc335fcfdef485c0b89f6934b4c1778853c1194a0845f21011fa88b8384c5"}``.

.. test:: clang-format reports no diff over the five current source and test files.
   :id: NEED_T025_M_SA_FORMAT

   Canonical ID: ``T025-M-SA-FORMAT``; revision: ``1``.

   clang-format reports no diff over the five current source and test files.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "ec0bc335fcfdef485c0b89f6934b4c1778853c1194a0845f21011fa88b8384c5"}``.

.. test:: Source review plus clang-tidy confirm every time decision routes through declare_clock/now/convert a
   :id: NEED_T025_M_SA_RAWCLOCK

   Canonical ID: ``T025-M-SA-RAWCLOCK``; revision: ``1``.

   Source review plus clang-tidy confirm every time decision routes through declare_clock/now/convert and no code path compares raw timestamps from different clock domains.

   Source: ``{"path": "src/xverse/xcom/src/validation_session.cpp", "sha256": "ac6b70183cfd1c3d00efdcaddaeadf9eb14cc55334a5dd9a3fa3719b681daa71"}``.

.. test:: The nm symbol enumeration of the static library exposes only xverse::xcom::validation and standard-l
   :id: NEED_T025_M_SA_SYMBOL

   Canonical ID: ``T025-M-SA-SYMBOL``; revision: ``1``.

   The nm symbol enumeration of the static library exposes only xverse::xcom::validation and standard-library weak symbols; no emission, transport, gateway, listener, journal, lease, dashboard, or persistent-store entry point exists.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "ec0bc335fcfdef485c0b89f6934b4c1778853c1194a0845f21011fa88b8384c5"}``.

.. test:: ThreadSanitizer is expected to report no data race for concurrent now/convert calls. NOT EXECUTED in
   :id: NEED_T025_M_SA_TSAN

   Canonical ID: ``T025-M-SA-TSAN``; revision: ``1``.

   ThreadSanitizer is expected to report no data race for concurrent now/convert calls. NOT EXECUTED in this sandbox: pending_protected_sanitizer_verification.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "ec0bc335fcfdef485c0b89f6934b4c1778853c1194a0845f21011fa88b8384c5"}``.

.. test:: DIA-01..DIA-06 pass: diagnostic precedence is ordered, stable, bounded, and payload-free.
   :id: NEED_T025_M_U_DIAGNOSTIC

   Canonical ID: ``T025-M-U-DIAGNOSTIC``; revision: ``1``.

   DIA-01..DIA-06 pass: diagnostic precedence is ordered, stable, bounded, and payload-free.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: NOM/HND/QUO/CON/NOMUT/ZEM manager cases pass: ordered validation before mutation, handle ownership, 
   :id: NEED_T025_M_U_MANAGER

   Canonical ID: ``T025-M-U-MANAGER``; revision: ``1``.

   NOM/HND/QUO/CON/NOMUT/ZEM manager cases pass: ordered validation before mutation, handle ownership, quota and capacity boundaries, deterministic concurrency, and a zero emission counter.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: PRM-01..PRM-09 and MIS-01..MIS-13 pass: immutable permit construction and the full single-field mism
   :id: NEED_T025_M_U_PERMIT

   Canonical ID: ``T025-M-U-PERMIT``; revision: ``1``.

   PRM-01..PRM-09 and MIS-01..MIS-13 pass: immutable permit construction and the full single-field mismatch matrix with the correct FieldLocator.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: REG-01..REG-06, RP-01..RP-05, and QUO-05 pass: controller-scoped exactly-once consumption, changed-n
   :id: NEED_T025_M_U_REGISTRY

   Canonical ID: ``T025-M-U-REGISTRY``; revision: ``1``.

   REG-01..REG-06, RP-01..RP-05, and QUO-05 pass: controller-scoped exactly-once consumption, changed-nonce replay rejection, and bounded bookkeeping exhaustion.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: LIF-01..LIF-16 pass: every lifecycle transition, terminal lockout, and safe idempotent repeat matche
   :id: NEED_T025_M_U_SESSION

   Canonical ID: ``T025-M-U-SESSION``; revision: ``1``.

   LIF-01..LIF-16 pass: every lifecycle transition, terminal lockout, and safe idempotent repeat matches the constexpr transition table.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: CLK-01..CLK-12 and CON-04 pass: declared domains, bounded reads, directed mapping with tolerance, an
   :id: NEED_T025_M_U_TIME

   Canonical ID: ``T025-M-U-TIME``; revision: ``1``.

   CLK-01..CLK-12 and CON-04 pass: declared domains, bounded reads, directed mapping with tolerance, and distinct regression/overflow failures; concurrent reads are deterministic.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: The seven F-02 transition rejection tests pass: each asserts the exact Result primary code and full 
   :id: NEED_T025_M_U_TRANSITION_REJECT

   Canonical ID: ``T025-M-U-TRANSITION-REJECT``; revision: ``1``.

   The seven F-02 transition rejection tests pass: each asserts the exact Result primary code and full snapshot equality (manager, session, consumed sets, counters, and mono/wall authority baselines) across the rejected transition.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: TYP-01..TYP-05 pass: the shared value vocabulary is closed and bounded and Diagnostic stays payload-
   :id: NEED_T025_M_U_TYPES

   Canonical ID: ``T025-M-U-TYPES``; revision: ``1``.

   TYP-01..TYP-05 pass: the shared value vocabulary is closed and bounded and Diagnostic stays payload-free within its size bound.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "3df3acdb6022c8f1c7d5a7113514ad24adf006893c3b1a0710fe597c5d7e3b7c"}``.

.. test:: Validation.EndToEndNominalScenario passes: the intended-use declared -> armed -> active -> closing -
   :id: NEED_T025_M_V_E2E

   Canonical ID: ``T025-M-V-E2E``; revision: ``1``.

   Validation.EndToEndNominalScenario passes: the intended-use declared -> armed -> active -> closing -> closed flow completes with declared time and action checks.

   Source: ``{"path": "tests/validation_session_validation_tests.cpp", "sha256": "6d0ffeec753aaca37fcd4dd1b1e7ce3cf93b9ee15784eb7ba333d63bb81daf5b"}``.

.. test:: Validation.ZEM_01 and Validation.ZEM_03 pass: the public symbol surface exposes no emission/transpor
   :id: NEED_T025_M_V_ZEM

   Canonical ID: ``T025-M-V-ZEM``; revision: ``1``.

   Validation.ZEM_01 and Validation.ZEM_03 pass: the public symbol surface exposes no emission/transport/journal/persistence entry point and the nominal path opens no file or socket.

   Source: ``{"path": "tests/validation_session_validation_tests.cpp", "sha256": "6d0ffeec753aaca37fcd4dd1b1e7ce3cf93b9ee15784eb7ba333d63bb81daf5b"}``.

.. req:: The authority must accept a finite set of declared clock domain identities and must report an unknow
   :id: NEED_T025_SR_001
   :links: NEED_T025_M_U_TIME, NEED_T025_STK_001, NEED_VALIDATION_TIME_AUTHORITY

   Canonical ID: ``T025-SR-001``; revision: ``1``.

   The authority must accept a finite set of declared clock domain identities and must report an unknown or undeclared domain as a distinct deterministic failure.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (time authority identifies clock domains); interface-bridge.md; anchors: XVE-SYS-0147, FR-015"}``.

.. req:: The authority must obtain current time for a declared domain from a host-supplied time source within
   :id: NEED_T025_SR_002
   :links: NEED_T025_M_U_TIME, NEED_T025_STK_001, NEED_VALIDATION_TIME_AUTHORITY

   Canonical ID: ``T025-SR-002``; revision: ``1``.

   The authority must obtain current time for a declared domain from a host-supplied time source within a bounded, explicit interval, and must report failure distinctly when the source is unavailable or returns an out-of-bounds value.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (obtains bounded current time); interface-bridge.md; anchors: XVE-SYS-0147, FR-015"}``.

.. req:: Converting a time from a source domain to a destination domain must require a declared mapping carry
   :id: NEED_T025_SR_003
   :links: NEED_T025_M_U_TIME, NEED_T025_STK_001, NEED_VALIDATION_TIME_AUTHORITY

   Canonical ID: ``T025-SR-003``; revision: ``1``.

   Converting a time from a source domain to a destination domain must require a declared mapping carrying source, destination, and maximum admissible tolerance; a missing mapping or a tolerance failure must return distinct deterministic results.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (maps between domains only under declared source, destination, and tolerance rules); interface-bridge.md; anchors: XVE-SYS-0147, FR-015"}``.

.. req:: The authority must detect monotonic regression in a domain and arithmetic overflow during conversion
   :id: NEED_T025_SR_004
   :links: NEED_T025_M_U_TIME, NEED_T025_STK_001, NEED_VALIDATION_TIME_AUTHORITY

   Canonical ID: ``T025-SR-004``; revision: ``1``.

   The authority must detect monotonic regression in a domain and arithmetic overflow during conversion, and must return distinct deterministic results for each.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (regression and overflow produce distinct deterministic results); interface-bridge.md; anchors: XVE-SYS-0147, FR-015"}``.

.. req:: Permit-validity and session-lifecycle time decisions must be expressed as authority queries in a sin
   :id: NEED_T025_SR_005
   :links: NEED_T025_M_I_CROSSDOMAIN, NEED_T025_M_U_TIME, NEED_T025_STK_001, NEED_VALIDATION_SESSION_MANAGER, NEED_VALIDATION_TIME_AUTHORITY

   Canonical ID: ``T025-SR-005``; revision: ``1``.

   Permit-validity and session-lifecycle time decisions must be expressed as authority queries in a single domain or through a declared mapping; raw timestamps from different domains must never be compared directly.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (raw timestamps from different domains are never compared); interface-bridge.md; anchors: FR-015, FR-033, XVE-SYS-0147"}``.

.. req:: The time authority must be non-copyable, must have an explicit documented lifetime, and must be safe
   :id: NEED_T025_SR_006
   :links: NEED_T025_M_SA_COMPILE, NEED_T025_M_U_TIME, NEED_T025_STK_006, NEED_VALIDATION_TIME_AUTHORITY

   Canonical ID: ``T025-SR-006``; revision: ``1``.

   The time authority must be non-copyable, must have an explicit documented lifetime, and must be safe for concurrent read/query use with deterministic results.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (define synchronization and lifetime rules, including whether the authority is non-copyable); interface-bridge.md REF-002; anchors: XVE-SYS-0147, FR-033"}``.

.. req:: A permit must be immutable once constructed and must bind exactly one session identity, plan digest,
   :id: NEED_T025_SR_007
   :links: NEED_T025_M_U_PERMIT, NEED_T025_STK_002, NEED_VALIDATION_PERMIT, NEED_VALIDATION_SESSION_MANAGER

   Canonical ID: ``T025-SR-007``; revision: ``1``.

   A permit must be immutable once constructed and must bind exactly one session identity, plan digest, scenario, deployment, environment, tool, interface, target, nonce, allowed action set, validity interval, and every finite quota or capacity.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (the immutable permit binds exactly one session identity, plan digest, ... every finite quota or capacity); interface-bridge.md REF-002; anchors: XVE-SYS-0152, XVE-SYS-0144, FR-016"}``.

.. req:: The allowed action set must be a closed, finite set; undefined action bits and composite values not 
   :id: NEED_T025_SR_008
   :links: NEED_T025_M_U_PERMIT, NEED_T025_M_U_TRANSITION_REJECT, NEED_T025_STK_002, NEED_VALIDATION_PERMIT

   Canonical ID: ``T025-SR-008``; revision: ``1``.

   The allowed action set must be a closed, finite set; undefined action bits and composite values not explicitly allowed must be rejected deterministically.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (reject undefined action bits or composite values that are not explicitly allowed); interface-bridge.md REF-002; anchors: FR-016"}``.

.. req:: Consumption must be controller-scoped and exactly-once: a consumed permit identity, or a session ide
   :id: NEED_T025_SR_009
   :links: NEED_T025_M_U_REGISTRY, NEED_T025_STK_002, NEED_VALIDATION_PERMIT_REGISTRY

   Canonical ID: ``T025-SR-009``; revision: ``1``.

   Consumption must be controller-scoped and exactly-once: a consumed permit identity, or a session identity already bound to a consumed permit, must not be consumed again, including when presented with a changed nonce.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (define a global or controller-scoped one-time-consumption rule; prevent duplicate exact permit or session identity from being consumed twice, including with a changed nonce); interface-bridge.md REF-002; anchors: XVE-SYS-0152, XVE-SYS-0144, FR-017"}``.

.. req:: Every finite quota or capacity bound carried by the permit and every bounded bookkeeping structure m
   :id: NEED_T025_SR_010
   :links: NEED_T025_M_U_MANAGER, NEED_T025_M_U_REGISTRY, NEED_T025_STK_002, NEED_VALIDATION_PERMIT_REGISTRY, NEED_VALIDATION_SESSION_MANAGER

   Canonical ID: ``T025-SR-010``; revision: ``1``.

   Every finite quota or capacity bound carried by the permit and every bounded bookkeeping structure must have an explicit exhaustion result and must never exceed its bound.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (return explicit exhaustion behavior; every finite quota or capacity); interface-bridge.md REF-002; anchors: XVE-SYS-0152, FR-017"}``.

.. req:: A session handle must bind a host-generated controller identity and a generation counter so that sta
   :id: NEED_T025_SR_011
   :links: NEED_T025_M_I_GENERATION, NEED_T025_M_U_MANAGER, NEED_T025_STK_003, NEED_VALIDATION_SESSION_MANAGER

   Canonical ID: ``T025-SR-011``; revision: ``1``.

   A session handle must bind a host-generated controller identity and a generation counter so that stale, foreign, and recreated-controller handles cannot authorise any operation.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (session handles bind a host-generated controller identity and generation so stale, foreign, and recreated-controller handles cannot authorize a record); interface-bridge.md REF-002; anchors: XVE-SYS-0144, XVE-SYS-0152, FR-018"}``.

.. req:: The lifecycle must expose declared to armed to active to closing to closed, with expired, revoked, a
   :id: NEED_T025_SR_012
   :links: NEED_T025_M_U_SESSION, NEED_T025_STK_003, NEED_VALIDATION_SESSION

   Canonical ID: ``T025-SR-012``; revision: ``1``.

   The lifecycle must expose declared to armed to active to closing to closed, with expired, revoked, and evidence-incomplete as terminal states, and must define which transitions are legal from each state.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (the lifecycle exposes declared, armed, active, closing, closed; expired, revoked, and evidence-incomplete are terminal); interface-bridge.md REF-002; anchors: XVE-SYS-0152, FR-018"}``.

.. req:: Validation of handle, context, time, and action must complete before any state mutation; safe idempo
   :id: NEED_T025_SR_013
   :links: NEED_T025_M_U_MANAGER, NEED_T025_M_U_SESSION, NEED_T025_STK_003, NEED_VALIDATION_SESSION

   Canonical ID: ``T025-SR-013``; revision: ``1``.

   Validation of handle, context, time, and action must complete before any state mutation; safe idempotent repeats must be accepted with a stable already-applied outcome and unsafe repeats must be rejected.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (define safe idempotency, reject unsafe repeats, and ensure validation of handle, context, time, and action precedes any state mutation); interface-bridge.md REF-002; anchors: XVE-SYS-0144, FR-019"}``.

.. req:: Live session capacity and controller/handle bookkeeping must be finite and host-configurable; creati
   :id: NEED_T025_SR_014
   :links: NEED_T025_M_U_MANAGER, NEED_T025_STK_006, NEED_VALIDATION_SESSION_MANAGER

   Canonical ID: ``T025-SR-014``; revision: ``1``.

   Live session capacity and controller/handle bookkeeping must be finite and host-configurable; creation beyond capacity must fail explicitly without leaking a handle.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (finite quotas or capacities; bounded session lifecycle); interface-bridge.md REF-002; anchors: XVE-SYS-0147, FR-033"}``.

.. req:: Every rejected operation must leave the affected session record, permit consumption bookkeeping, cou
   :id: NEED_T025_SR_015
   :links: NEED_T025_M_U_MANAGER, NEED_T025_M_U_TRANSITION_REJECT, NEED_T025_STK_004, NEED_VALIDATION_SESSION, NEED_VALIDATION_SESSION_MANAGER

   Canonical ID: ``T025-SR-015``; revision: ``1``.

   Every rejected operation must leave the affected session record, permit consumption bookkeeping, counters, and authority state unchanged.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (rejected operations leave state unchanged); interface-bridge.md REF-002; anchors: XVE-SYS-0154, FR-019"}``.

.. req:: Diagnostics must be returned as an ordered sequence of stable, enumerable codes with no payload, ite
   :id: NEED_T025_SR_016
   :links: NEED_T025_M_U_DIAGNOSTIC, NEED_T025_STK_004, NEED_VALIDATION_DIAGNOSTIC

   Canonical ID: ``T025-SR-016``; revision: ``1``.

   Diagnostics must be returned as an ordered sequence of stable, enumerable codes with no payload, item, observation, or free-form content, and multi-failure ordering must follow a declared precedence.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (produce stable, ordered, payload-free diagnostics); interface-bridge.md REF-002; anchors: XVE-SYS-0154, FR-020"}``.

.. req:: Concurrent permit consumption and concurrent session mutation must be atomic with respect to shared 
   :id: NEED_T025_SR_017
   :links: NEED_T025_M_I_CONTROLLER, NEED_T025_M_U_MANAGER, NEED_T025_STK_006, NEED_VALIDATION_PERMIT_REGISTRY, NEED_VALIDATION_SESSION_MANAGER

   Canonical ID: ``T025-SR-017``; revision: ``1``.

   Concurrent permit consumption and concurrent session mutation must be atomic with respect to shared state, producing deterministic outcomes with exactly one success where the operation is exactly-once.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (explicit time authority; deterministic concurrency; synchronization rules); interface-bridge.md REF-002; anchors: XVE-SYS-0147, FR-033"}``.

.. req:: The candidate must not expose or perform any normal-route emission: no communication item, transport
   :id: NEED_T025_SR_018
   :links: NEED_T025_M_SA_SYMBOL, NEED_T025_M_V_ZEM, NEED_T025_STK_005, NEED_VALIDATION_SESSION_MANAGER

   Canonical ID: ``T025-SR-018``; revision: ``1``.

   The candidate must not expose or perform any normal-route emission: no communication item, transport, gateway, network listener, journal, lease, dashboard, persistent store, or external service, and no logging or telemetry in the nominal path.

   Source: ``{"kind": "admitted_packet", "reference": "packet.md (the foundation must neither emit a communication item nor create a transport, gateway, network listener, journal, lease, dashboard, persistent store, or external service; all normal-route emission counts remain zero); anchors: FR-020"}``.

.. req:: All permit-validity and session-lifecycle time decisions must be made through a single explicit time
   :id: NEED_T025_STK_001

   Canonical ID: ``T025-STK-001``; revision: ``1``.

   All permit-validity and session-lifecycle time decisions must be made through a single explicit time authority that knows its clock domains and only compares times within one domain or through a declared mapping.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (time-authority clause); interface-bridge.md; anchors: XVE-SYS-0147, FR-015, FR-033"}``.

.. req:: A host-controlled local validation permit must bind exactly one session and its complete operational
   :id: NEED_T025_STK_002

   Canonical ID: ``T025-STK-002``; revision: ``1``.

   A host-controlled local validation permit must bind exactly one session and its complete operational envelope, and must be consumed at most once.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (immutable permit / one-time consumption clause); interface-bridge.md REF-002; anchors: XVE-SYS-0152, XVE-SYS-0144, FR-016, FR-017"}``.

.. req:: A validation session is created by a host-generated controller identity, is addressed by a handle bo
   :id: NEED_T025_STK_003

   Canonical ID: ``T025-STK-003``; revision: ``1``.

   A validation session is created by a host-generated controller identity, is addressed by a handle bound to that controller identity and a generation, and moves only through the defined lifecycle and terminal states.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (session handle / lifecycle clause); interface-bridge.md REF-002; anchors: XVE-SYS-0144, XVE-SYS-0152, FR-018"}``.

.. req:: Any rejected operation leaves the affected session and permit state unchanged and produces a stable,
   :id: NEED_T025_STK_004

   Canonical ID: ``T025-STK-004``; revision: ``1``.

   Any rejected operation leaves the affected session and permit state unchanged and produces a stable, ordered diagnostic that carries no payload.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (rejection / diagnostics clause); interface-bridge.md REF-002; anchors: XVE-SYS-0154, FR-019, FR-020"}``.

.. req:: The normal route must emit zero communication items, zero telemetry, zero network traffic, and zero 
   :id: NEED_T025_STK_005

   Canonical ID: ``T025-STK-005``; revision: ``1``.

   The normal route must emit zero communication items, zero telemetry, zero network traffic, and zero persisted records.

   Source: ``{"kind": "admitted_packet", "reference": "packet.md (no emission / no transport clause); anchors: FR-020"}``.

.. req:: The foundation's memory, permit bookkeeping, and session capacity are finite and configurable, and c
   :id: NEED_T025_STK_006

   Canonical ID: ``T025-STK-006``; revision: ``1``.

   The foundation's memory, permit bookkeeping, and session capacity are finite and configurable, and concurrent use yields deterministic results without duplicate consumption.

   Source: ``{"kind": "admitted_packet_and_bridge", "reference": "packet.md (synchronization and lifetime clause); interface-bridge.md REF-002; anchors: XVE-SYS-0147, FR-033"}``.

.. unit:: Own the single deterministic diagnostic precedence order over the Result enum and the construction o
   :id: NEED_T025_U_DIAGNOSTIC
   :links: NEED_T025_M_SA_CLANGTIDY, NEED_T025_M_SA_COMPILE, NEED_T025_M_U_DIAGNOSTIC

   Canonical ID: ``T025-U-DIAGNOSTIC``; revision: ``1``.

   Own the single deterministic diagnostic precedence order over the Result enum and the construction of ordered, stable, payload-free code sequences with at most one bounded numeric locator.

.. unit:: Own controller identity and generation, bounded live-session capacity, handle issuance, and the sing
   :id: NEED_T025_U_MANAGER
   :links: NEED_T025_M_SA_COMPILE, NEED_T025_M_SA_SYMBOL, NEED_T025_M_U_MANAGER, NEED_T025_M_U_TRANSITION_REJECT

   Canonical ID: ``T025-U-MANAGER``; revision: ``1``.

   Own controller identity and generation, bounded live-session capacity, handle issuance, and the single ordered validation path (handle, context, time, action) that precedes every mutation, exposing a zero normal-route emission counter.

.. unit:: Model the immutable host-issued permit binding exactly one session identity and its full operational
   :id: NEED_T025_U_PERMIT
   :links: NEED_T025_M_SA_CLANGTIDY, NEED_T025_M_SA_COMPILE, NEED_T025_M_U_PERMIT

   Canonical ID: ``T025-U-PERMIT``; revision: ``1``.

   Model the immutable host-issued permit binding exactly one session identity and its full operational envelope, with a stable FNV-1a content identity and a closed allowed-action set, plus the builder that validates construction and the SessionContext runtime envelope.

.. unit:: Enforce controller-scoped, exactly-once permit consumption and bounded consumed-identity bookkeeping
   :id: NEED_T025_U_REGISTRY
   :links: NEED_T025_M_SA_CLANGTIDY, NEED_T025_M_SA_COMPILE, NEED_T025_M_U_REGISTRY

   Canonical ID: ``T025-U-REGISTRY``; revision: ``1``.

   Enforce controller-scoped, exactly-once permit consumption and bounded consumed-identity bookkeeping with an explicit exhaustion result, independent of the session table.

.. unit:: Own the bounded lifecycle state of one validation session and the pure transition table with safe-id
   :id: NEED_T025_U_SESSION
   :links: NEED_T025_M_SA_CLANGTIDY, NEED_T025_M_SA_COMPILE, NEED_T025_M_U_SESSION

   Canonical ID: ``T025-U-SESSION``; revision: ``1``.

   Own the bounded lifecycle state of one validation session and the pure transition table with safe-idempotency, unsafe-repeat, terminal-lockout, and quota-decrement rules.

.. unit:: Own the declared clock domains, bounded current-time acquisition, directed source-to-destination map
   :id: NEED_T025_U_TIME
   :links: NEED_T025_M_SA_COMPILE, NEED_T025_M_SA_RAWCLOCK, NEED_T025_M_SA_TSAN, NEED_T025_M_U_TIME

   Canonical ID: ``T025-U-TIME``; revision: ``1``.

   Own the declared clock domains, bounded current-time acquisition, directed source-to-destination mappings with tolerance, and the distinct regression/overflow/unknown/missing-mapping outcomes.

.. unit:: Define the closed, bounded value vocabulary shared by every T025 unit: clock/timestamp/permit/sessio
   :id: NEED_T025_U_TYPES
   :links: NEED_T025_M_SA_CLANGTIDY, NEED_T025_M_SA_COMPILE, NEED_T025_M_SA_DOXYGEN, NEED_T025_M_U_TYPES

   Canonical ID: ``T025-U-TYPES``; revision: ``1``.

   Define the closed, bounded value vocabulary shared by every T025 unit: clock/timestamp/permit/session/controller identities, result codes, lifecycle states, actions, quotas, the field-locator enum, the payload-free Diagnostic value type, and the deterministic FNV-1a 128-bit content digest.

.. scenario:: A host consumes a valid permit and drives one session declared -> armed -> active -> closing -> clos
   :id: NEED_T025_VS_001
   :links: NEED_T025_STK_003, NEED_T025_STK_005

   Canonical ID: ``T025-VS-001``; revision: ``1``.

   A host consumes a valid permit and drives one session declared -> armed -> active -> closing -> closed using only declared time and allowed actions, observing zero normal-route emissions.

.. scenario:: A permit whose validity interval is declared in another clock domain is accepted only after a declar
   :id: NEED_T025_VS_002
   :links: NEED_T025_STK_001

   Canonical ID: ``T025-VS-002``; revision: ``1``.

   A permit whose validity interval is declared in another clock domain is accepted only after a declared source->destination mapping resolves the caller's time, and is rejected with MissingMapping when no mapping is declared.

.. scenario:: After a permit is consumed once, re-presenting the same permit identity, the same session identity w
   :id: NEED_T025_VS_003
   :links: NEED_T025_STK_002

   Canonical ID: ``T025-VS-003``; revision: ``1``.

   After a permit is consumed once, re-presenting the same permit identity, the same session identity with a changed nonce, or the permit bound to another session is rejected with a distinct, stable result.

.. scenario:: A stale-generation handle, a foreign-controller handle, a handle from a recreated controller, and a 
   :id: NEED_T025_VS_004
   :links: NEED_T025_STK_003

   Canonical ID: ``T025-VS-004``; revision: ``1``.

   A stale-generation handle, a foreign-controller handle, a handle from a recreated controller, and a forged handle all fail to authorise a transition, and no other live session changes state.

.. scenario:: The public surface exposes no emission, transport, journal, or persistence entry point, the nominal 
   :id: NEED_T025_VS_005
   :links: NEED_T025_STK_005

   Canonical ID: ``T025-VS-005``; revision: ``1``.

   The public surface exposes no emission, transport, journal, or persistence entry point, the nominal path opens no file or socket, and the reported normal-route emission counter stays zero.

.. scenario:: Consuming at the last available quota unit or the last session slot succeeds, and the next attempt r
   :id: NEED_T025_VS_006
   :links: NEED_T025_STK_002, NEED_T025_STK_006

   Canonical ID: ``T025-VS-006``; revision: ``1``.

   Consuming at the last available quota unit or the last session slot succeeds, and the next attempt returns an explicit QuotaExhausted or CapacityExhausted result without partial mutation.

.. scenario:: Every rejected operation (permit mismatch, replay, clock failure, handle failure, invalid or termina
   :id: NEED_T025_VS_007
   :links: NEED_T025_STK_004

   Canonical ID: ``T025-VS-007``; revision: ``1``.

   Every rejected operation (permit mismatch, replay, clock failure, handle failure, invalid or terminal transition) leaves manager, session, consumed-set, counter, and authority-baseline state byte-identical and returns an ordered, payload-free diagnostic.

.. scenario:: Concurrent attempts to consume one permit yield exactly one success; concurrent attempts to apply th
   :id: NEED_T025_VS_008
   :links: NEED_T025_STK_006

   Canonical ID: ``T025-VS-008``; revision: ``1``.

   Concurrent attempts to consume one permit yield exactly one success; concurrent attempts to apply the same transition yield one applied mutation and deterministic already-applied repeats without corrupting state.

.. comp:: Own the deterministic diagnostic precedence and the construction of ordered, stable, payload-free co
   :id: NEED_VALIDATION_DIAGNOSTIC
   :links: NEED_T025_U_DIAGNOSTIC

   Canonical ID: ``validation_diagnostic``; revision: ``1``.

   Own the deterministic diagnostic precedence and the construction of ordered, stable, payload-free code sequences.

.. comp:: Model the immutable, host-issued permit that binds exactly one session identity and its full operati
   :id: NEED_VALIDATION_PERMIT
   :links: NEED_T025_U_PERMIT

   Canonical ID: ``validation_permit``; revision: ``1``.

   Model the immutable, host-issued permit that binds exactly one session identity and its full operational envelope, with a stable content identity and a closed allowed-action set.

.. comp:: Enforce controller-scoped, exactly-once permit consumption and bounded consumed-identity bookkeeping
   :id: NEED_VALIDATION_PERMIT_REGISTRY
   :links: NEED_T025_U_REGISTRY

   Canonical ID: ``validation_permit_registry``; revision: ``1``.

   Enforce controller-scoped, exactly-once permit consumption and bounded consumed-identity bookkeeping, returning explicit exhaustion results.

.. comp:: Own the bounded lifecycle state of one validation session and the safe-idempotency, unsafe-repeat, a
   :id: NEED_VALIDATION_SESSION
   :links: NEED_T025_U_SESSION

   Canonical ID: ``validation_session``; revision: ``1``.

   Own the bounded lifecycle state of one validation session and the safe-idempotency, unsafe-repeat, and terminal-lockout rules.

.. comp:: Own controller identity and generation, bounded live-session capacity, handle issuance, and the sing
   :id: NEED_VALIDATION_SESSION_MANAGER
   :links: NEED_T025_U_MANAGER

   Canonical ID: ``validation_session_manager``; revision: ``1``.

   Own controller identity and generation, bounded live-session capacity, handle issuance, and the single ordered validation path (handle, context, time, action) that precedes every mutation.

.. comp:: Own the declared clock domains, bounded current-time acquisition, directed source-to-destination map
   :id: NEED_VALIDATION_TIME_AUTHORITY
   :links: NEED_T025_U_TIME

   Canonical ID: ``validation_time_authority``; revision: ``1``.

   Own the declared clock domains, bounded current-time acquisition, directed source-to-destination mappings with tolerance, and the distinct regression/overflow/unknown/missing-mapping outcomes.

.. comp:: Define the closed, bounded vocabulary shared by every T025 component: identifiers, timestamps, resul
   :id: NEED_VALIDATION_TYPES
   :links: NEED_T025_U_TYPES

   Canonical ID: ``validation_types``; revision: ``1``.

   Define the closed, bounded vocabulary shared by every T025 component: identifiers, timestamps, result codes, diagnostics, actions, lifecycle states, and the field-locator enum.
