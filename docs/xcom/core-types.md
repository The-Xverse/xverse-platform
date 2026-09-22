# X-COM core types

Status: prototype core value-model slice, READY_FOR_REVIEW. This is capability-007 Phase 3 slice 1
and is not accepted production software.

## Scope and public contract

The `xverse::xcom_core_types` CMake target provides C++20 value-owned contracts, communication
items, bounded identities/versions/payloads, explicit success-or-diagnostic results, and stable
deterministically ordered diagnostics. Consumers may use the target alias `xverse::xcom_core_types`
and include `<xverse/xcom/core_types.hpp>`.

Logical contract identity is independent of provider, protocol, address, and physical realization.
Provider and route identities are required item provenance fields only; they do not define the
logical contract. The four retained interaction kinds and compatible directions are:

| Interaction kind | Source direction | Target direction |
|---|---|---|
| signal/state update | produce | consume |
| message/event | produce | consume |
| service request | request | respond |
| service response | respond | request |

`CommunicationContract::create` and `CommunicationItem::create` copy all caller input into bounded
fixed-capacity storage and return either one fully validated immutable value or one non-empty
immutable `DiagnosticSet`. Validated construction and rejection allocate no memory and are
`noexcept`; allocation failure therefore cannot escape these factories. Values expose const access
only. Copy construction is supported, including construction from an rvalue, and leaves the source
valid and unchanged. Assignment is disabled so an accessor view cannot be invalidated while its
owner remains alive. Concurrent const reads are safe; separate result/value instances require no
shared state. Accessor views and spans remain valid until their owning value is destroyed.

## Explicit bounds and failures

- identities: 1–128 bytes, no ASCII control bytes or leading/trailing ASCII whitespace; other
  bytes are validated byte-for-byte without consulting the caller's C locale;
- versions: 1–32 bytes in canonical decimal `major.minor.patch` form, without leading zeroes;
- payload: 0–65,536 bytes, copied into the item;
- diagnostic reason and correction: 1–256 bytes each.
- diagnostic set: 1–32 entries; the contract and item validation matrices produce at most 6 and 19.

Stable codes are `XCOM-TYPE-E001` (required field), `XCOM-TYPE-E002` (bound or lexical identity),
`XCOM-TYPE-E003` (version), `XCOM-TYPE-E004` (interaction/direction compatibility), and
`XCOM-TYPE-E005` (item/contract mismatch). Diagnostics carry severity, validation phase, affected
identity, reason, correction, and a deterministic lexical ordering key. Their serialization escapes
separators and is byte-stable for an equivalent invalid input set.

`Diagnostic::serialize` and `DiagnosticSet::serialize` are reporting conveniences that return a
dynamic `std::string`; unlike validated construction, they may propagate `std::bad_alloc`. Consumers
that require allocation-free inspection use `ordering_key()` and `values()` instead. The explicit
65,536-byte payload capacity makes item and successful-result objects correspondingly large; this is
the bounded storage tradeoff that preserves exception-free construction in this prototype slice.

Factories do not perform network discovery, ambient configuration or secret lookup, legacy access,
filesystem access, or process execution. They do not provide cross-clock comparison: an item carries
one timestamp and one explicit clock-domain identity without inferring comparability.

## Build and verification

The root build conditionally includes `src/xverse/xcom` and preserves the previously admitted offline
dependency envelope. The core-types target uses only the C++ standard library and adds no package.
With the admitted environment variables set:

```sh
python3 scripts/validate_xcom_core_types.py --unit
python3 scripts/validate_xcom_core_types.py --lint
python3 scripts/validate_xcom_core_types.py --static
python3 scripts/validate_xcom_core_types.py --integration
python3 scripts/validate_xcom_core_types.py --all
```

The validation driver creates disposable Ninja build trees. Its unit fixture compares construction
outcomes after changing the caller's C character-classification locale, and its source scan rejects
locale-sensitive C classification APIs in production units. The static and lint gates use the
admitted toolchain's clang-tidy and the existing repository documentation validator. That validator
checks Python docstrings, proves its own rejection behavior, preserves repository-wide Python source
coverage, and generates warning-free Doxygen HTML/XML under ignored `build/doxygen`. A separate
strict Doxygen pass rejects undocumented owned C++ declarations and parameters without weakening
the repository-wide Python documentation configuration.
The external-consumer CTest fixture includes only the public umbrella header, links only the public
target, and checks both successful item construction and exact diagnostic fields.

Bidirectional requirement/design/code/test/check mappings are in
`docs/xcom/core-types-traceability.json`. Evidence is bound to baseline `BASE-fbdb289a1d9423976d6e`
and, at verification time, to the host-owned `SESN_CANDIDATE_REVISION`. The validator requires a full
lowercase Git SHA and confirms that it equals the workspace `HEAD`; SESN's network-disabled
verification and independent review records remain external review evidence.

## Excluded behavior and maturity

This slice implements no endpoint or route lifecycle, provider, transport, XDL plan compiler,
observation, stimulation, time authority, journal, lease, gRPC/gateway, Argus/Maestro/Faults,
compatibility adapter, discovery, or live-readiness behavior. Provider and route identity fields do
not establish either subsystem. The fixture demonstrates owned value semantics only and makes no
network, timing, protocol, compatibility, or production-readiness claim.
