Engineering traceability
========================

Generated from canonical engineering JSON records.

.. test:: Integration.IndependentControllerScopes passes: consumption and lifecycle bookkeeping stay isolated 
   :id: NEED_T025_M_I_CONTROLLER

   Canonical ID: ``T025-M-I-CONTROLLER``; revision: ``1``.

   Integration.IndependentControllerScopes passes: consumption and lifecycle bookkeeping stay isolated across independent controller scopes.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "547b9d0feb8b08b8c05495dbc4a2bbeb773e9897a2fa83301c68701b20052ce4"}``.

.. test:: Integration.MappedValidityCrossDomainLifecycle passes: a permit validity interval expressed in anoth
   :id: NEED_T025_M_I_CROSSDOMAIN

   Canonical ID: ``T025-M-I-CROSSDOMAIN``; revision: ``1``.

   Integration.MappedValidityCrossDomainLifecycle passes: a permit validity interval expressed in another domain is resolved only through a declared mapping and drives the lifecycle.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "547b9d0feb8b08b8c05495dbc4a2bbeb773e9897a2fa83301c68701b20052ce4"}``.

.. test:: Integration.GenerationRotationInvalidatesLiveHandle passes: advancing a controller generation invali
   :id: NEED_T025_M_I_GENERATION

   Canonical ID: ``T025-M-I-GENERATION``; revision: ``1``.

   Integration.GenerationRotationInvalidatesLiveHandle passes: advancing a controller generation invalidates previously issued handles without perturbing other sessions.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "547b9d0feb8b08b8c05495dbc4a2bbeb773e9897a2fa83301c68701b20052ce4"}``.

.. test:: Integration.QuotaExhaustionThroughTransitionPath passes: quota exhaustion through the transition pat
   :id: NEED_T025_M_I_QUOTA

   Canonical ID: ``T025-M-I-QUOTA``; revision: ``1``.

   Integration.QuotaExhaustionThroughTransitionPath passes: quota exhaustion through the transition path is explicit and non-mutating.

   Source: ``{"path": "tests/validation_session_integration_tests.cpp", "sha256": "547b9d0feb8b08b8c05495dbc4a2bbeb773e9897a2fa83301c68701b20052ce4"}``.

.. test:: clang-tidy reports no diagnostic over the eight enabled rules (bugprone-branch-clone, cppcoreguideli
   :id: NEED_T025_M_SA_CLANGTIDY

   Canonical ID: ``T025-M-SA-CLANGTIDY``; revision: ``1``.

   clang-tidy reports no diagnostic over the eight enabled rules (bugprone-branch-clone, cppcoreguidelines-pro-type-member-init, cppcoreguidelines-special-member-functions, misc-const-correctness, modernize-use-nodiscard, performance-unnecessary-copy-initialization, performance-unnecessary-value-param, readability-make-member-function-const).

   Source: ``{"path": "src/xverse/xcom/src/validation_session.cpp", "sha256": "c3a62ab4c807b5df263ab8412d5c31201a84eebe70ae41e0aa93fb0928eec08f"}``.

.. test:: Compile-time static_asserts hold: non-copyability/non-movability of TimeAuthority, PermitRegistry, a
   :id: NEED_T025_M_SA_COMPILE

   Canonical ID: ``T025-M-SA-COMPILE``; revision: ``1``.

   Compile-time static_asserts hold: non-copyability/non-movability of TimeAuthority, PermitRegistry, and SessionManager; the exhaustive constexpr transition table; permit immutability; diagnostic payload-freedom and size bound.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "a8bbfb14e25f07ff45a65e87a172ccaf52b55847764a4daa5e8f5930a3f5fa20"}``.

.. test:: gcovr line coverage of the candidate is reported (observed 92.4% of 846 lines) with reports/coverage
   :id: NEED_T025_M_SA_COVERAGE

   Canonical ID: ``T025-M-SA-COVERAGE``; revision: ``1``.

   gcovr line coverage of the candidate is reported (observed 92.4% of 846 lines) with reports/coverage-summary.json; no coverage threshold beyond reporting is asserted by the admitted packet.

   Source: ``{"path": "src/xverse/xcom/src/validation_session.cpp", "sha256": "c3a62ab4c807b5df263ab8412d5c31201a84eebe70ae41e0aa93fb0928eec08f"}``.

.. test:: Doxygen builds with WARN_AS_ERROR=YES: every public symbol carries a brief, and every public symbol 
   :id: NEED_T025_M_SA_DOXYGEN

   Canonical ID: ``T025-M-SA-DOXYGEN``; revision: ``1``.

   Doxygen builds with WARN_AS_ERROR=YES: every public symbol carries a brief, and every public symbol maps to its owning unit specification (observed 395 symbols, audit issues []).

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "a8bbfb14e25f07ff45a65e87a172ccaf52b55847764a4daa5e8f5930a3f5fa20"}``.

.. test:: clang-format --dry-run --Werror is clean over the header, source, and all three test files against t
   :id: NEED_T025_M_SA_FORMAT

   Canonical ID: ``T025-M-SA-FORMAT``; revision: ``1``.

   clang-format --dry-run --Werror is clean over the header, source, and all three test files against the project .clang-format.

   Source: ``{"path": "src/xverse/xcom/src/validation_session.cpp", "sha256": "c3a62ab4c807b5df263ab8412d5c31201a84eebe70ae41e0aa93fb0928eec08f"}``.

.. test:: Source scan and clang-tidy review find no comparison of a raw timestamp from one clock domain with a
   :id: NEED_T025_M_SA_RAWCLOCK

   Canonical ID: ``T025-M-SA-RAWCLOCK``; revision: ``1``.

   Source scan and clang-tidy review find no comparison of a raw timestamp from one clock domain with a raw timestamp from another domain; all cross-domain decisions resolve through TimeAuthority.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "a8bbfb14e25f07ff45a65e87a172ccaf52b55847764a4daa5e8f5930a3f5fa20"}``.

.. test:: nm symbol enumeration over libxverse_validation.a reports only xverse::xcom::validation symbols; no 
   :id: NEED_T025_M_SA_SYMBOL

   Canonical ID: ``T025-M-SA-SYMBOL``; revision: ``1``.

   nm symbol enumeration over libxverse_validation.a reports only xverse::xcom::validation symbols; no emission, transport, gateway, listener, journal, lease, dashboard, or persistent-store entry point exists.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "a8bbfb14e25f07ff45a65e87a172ccaf52b55847764a4daa5e8f5930a3f5fa20"}``.

.. test:: ThreadSanitizer is expected to report no data race for concurrent now/convert calls. NOT EXECUTED in
   :id: NEED_T025_M_SA_TSAN

   Canonical ID: ``T025-M-SA-TSAN``; revision: ``1``.

   ThreadSanitizer is expected to report no data race for concurrent now/convert calls. NOT EXECUTED in this sandbox: pending_protected_sanitizer_verification.

   Source: ``{"path": "src/xverse/xcom/include/xverse/xcom/validation_session.hpp", "sha256": "a8bbfb14e25f07ff45a65e87a172ccaf52b55847764a4daa5e8f5930a3f5fa20"}``.

.. test:: DIA-01..DIA-06 pass: diagnostics are payload-free, bounded, and ordered by the declared Result prece
   :id: NEED_T025_M_U_DIAGNOSTIC

   Canonical ID: ``T025-M-U-DIAGNOSTIC``; revision: ``1``.

   DIA-01..DIA-06 pass: diagnostics are payload-free, bounded, and ordered by the declared Result precedence.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: NOM/MIS/RP/QUO/HND/CON/NOMUT/ZEM/ADV manager cases pass: ordered validation before mutation, handle 
   :id: NEED_T025_M_U_MANAGER

   Canonical ID: ``T025-M-U-MANAGER``; revision: ``1``.

   NOM/MIS/RP/QUO/HND/CON/NOMUT/ZEM/ADV manager cases pass: ordered validation before mutation, handle ownership and recreation, quota and capacity boundaries, deterministic concurrency, and a zero emission counter.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: PRM-01..PRM-09 pass: immutable permit construction binds exactly one session envelope and rejects un
   :id: NEED_T025_M_U_PERMIT

   Canonical ID: ``T025-M-U-PERMIT``; revision: ``1``.

   PRM-01..PRM-09 pass: immutable permit construction binds exactly one session envelope and rejects undefined or composite action values.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: REG-01..REG-04, REG-06, and QUO-05 pass: controller-scoped exactly-once consumption, atomic check-th
   :id: NEED_T025_M_U_REGISTRY

   Canonical ID: ``T025-M-U-REGISTRY``; revision: ``1``.

   REG-01..REG-04, REG-06, and QUO-05 pass: controller-scoped exactly-once consumption, atomic check-then-insert, and bounded bookkeeping exhaustion.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: LIF-01..LIF-16, QUO-01, and QUO-02 pass: every lifecycle transition, terminal lockout, safe idempote
   :id: NEED_T025_M_U_SESSION

   Canonical ID: ``T025-M-U-SESSION``; revision: ``1``.

   LIF-01..LIF-16, QUO-01, and QUO-02 pass: every lifecycle transition, terminal lockout, safe idempotent repeat, and quota boundary matches the constexpr transition table.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: CLK-01..CLK-17, ADV-R3/ADV-R4, and CON-04 pass: declared domains, bounded reads, directed mapping wi
   :id: NEED_T025_M_U_TIME

   Canonical ID: ``T025-M-U-TIME``; revision: ``1``.

   CLK-01..CLK-17, ADV-R3/ADV-R4, and CON-04 pass: declared domains, bounded reads, directed mapping with tolerance, distinct regression/overflow failures, full-range tolerance arithmetic, and non-mutating rejected conversion.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: The ten repair regression tests pass: transition-path time/action rejections leave manager, session,
   :id: NEED_T025_M_U_TRANSITION_REJECT

   Canonical ID: ``T025-M-U-TRANSITION-REJECT``; revision: ``1``.

   The ten repair regression tests pass: transition-path time/action rejections leave manager, session, consumed sets, counters, and both authority baselines byte-identical (F-02 class), and replay on a full live-session table reports SessionAlreadyConsumed/PermitAlreadyConsumed before capacity, with the unconsumed-permit capacity rejection transactional (F-IMP-01).

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: TYP-01..TYP-06 pass: the shared value vocabulary (ids, digests, action-mask helpers, enums) is stabl
   :id: NEED_T025_M_U_TYPES

   Canonical ID: ``T025-M-U-TYPES``; revision: ``1``.

   TYP-01..TYP-06 pass: the shared value vocabulary (ids, digests, action-mask helpers, enums) is stable and preserves its documented invariants.

   Source: ``{"path": "tests/validation_session_tests.cpp", "sha256": "eaf4cb469a8de39fc289c90e58b3600879903839894fafd82d2d9c95e0a0d2fb"}``.

.. test:: Validation.EndToEndNominalScenario passes: one permit drives a full declared->armed->active->closing
   :id: NEED_T025_M_V_E2E

   Canonical ID: ``T025-M-V-E2E``; revision: ``1``.

   Validation.EndToEndNominalScenario passes: one permit drives a full declared->armed->active->closing->closed lifecycle with zero normal-route emissions.

   Source: ``{"path": "tests/validation_session_validation_tests.cpp", "sha256": "5ed87a0f82e6686f2bdcb606d72d53d077599bc5c904643de5c54f89671f2eb9"}``.

.. test:: Validation.ZEM_01 and Validation.ZEM_03 pass: the reported normal-route emission counter is zero and
   :id: NEED_T025_M_V_ZEM

   Canonical ID: ``T025-M-V-ZEM``; revision: ``1``.

   Validation.ZEM_01 and Validation.ZEM_03 pass: the reported normal-route emission counter is zero and the nominal path opens no file or socket (file-descriptor delta zero).

   Source: ``{"path": "tests/validation_session_validation_tests.cpp", "sha256": "5ed87a0f82e6686f2bdcb606d72d53d077599bc5c904643de5c54f89671f2eb9"}``.

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

.. unit:: Own the host-issued manager uniqueness scope, controller identity and generation, bounded live-sessi
   :id: NEED_T025_U_MANAGER
   :links: NEED_T025_M_SA_COMPILE, NEED_T025_M_SA_SYMBOL, NEED_T025_M_U_MANAGER, NEED_T025_M_U_TRANSITION_REJECT

   Canonical ID: ``T025-U-MANAGER``; revision: ``1``.

   Own the host-issued manager uniqueness scope, controller identity and generation, bounded live-session capacity, scope-bound handle issuance, and the single ordered validation path (handle, context, time, action) that precedes every mutation, resolving every time decision through the authority and exposing a zero normal-route emission counter.

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

   Define the closed, bounded value vocabulary shared by every T025 unit: clock/timestamp/permit/session/controller identities plus the manager uniqueness scope, result codes, lifecycle states, actions, quotas, the field-locator enum, the payload-free Diagnostic value type, and the deterministic FNV-1a 128-bit content digest.

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
