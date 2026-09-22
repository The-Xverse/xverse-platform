# SD-0001 static interface audit

**Date**: 2026-09-21

**Scope**: Read-only inspection of the frozen source and reproducible candidate bundle already
authorized for SD-0001. No gateway, middleware, peer, network interface, test tool, or production
workload was executed. Exact route identifiers, endpoint values, payload values, and private
infrastructure details are withheld.

**Result**: The audit supplies a bounded source/configuration contract projection. It does not verify
protocol interoperability, readiness, shutdown, timing, or application behavior, and it does not
close `XVERSE-PLAN-INTERFACE-CONTRACT-UNVERIFIED`.

Machine-readable public summary: [`SD-0001-interface-evidence.json`](SD-0001-interface-evidence.json),
SHA-256 `894d8b8e3abd68bfe403b6206d0f4f54d79d361e1507d3e1300e035d5e534d51`.

## Evidence identity

| Evidence | SHA-256 or immutable identity |
|---|---|
| Legacy source commit | `7c393c9f5a49239c76122486c49cb1993164475c` |
| Legacy source tree | `4aab3e623a293626b44a9d8e33c05a307bf51956` |
| Candidate gateway | `1fcf49058ff358dc7e81b11f18f4f288c709409b1ac0d9d7f3258b6e12b4b7c2` |
| Selected mapping | `198529ddb125a7eb069c69b6dc1b7de5267f192b162e28ac97dd4099462c7232` |
| Selected vsomeip configuration | `332db003c2f2038ceb10dc67b353fd99539eca001c8305b6c58f1ba36a34f144` |
| CMake definition | `6353a171c6bb2d5039d05a77d86d2cad506f900174cc5329de1d7d5caf9f3635` |
| Gateway entry point | `9b2196eac7d792f874dcc8acdca5b841056ab5eed1618391b8b62aff5eced672` |
| Mapping implementation/header | `c1abbd765787af77e2e3e47c753ac1883118866ca298fdedb53e145412551bbf` / `918784d00f8acdfeb2877056aabe67787c64a101424d53948d354d9de7139aa9` |
| Router implementation/header | `85cfd05d13ecd392d2601a59435b3b6993cd236c2aa363a610d2406d46b30d79` / `8adc0c84c16b88bfd600f57a53407b1f26b5412ea123a732cd548db9492fe64d` |
| SOME/IP implementation/header | `3d043b05226087bfaa35601da02c20d13fba8ba487504412a22e3bb04c2e1434` / `0cd4ccfd73be2496334ea8dfbe7b140bb8a44b4725e0eaf7b543711eedc749c1` |
| Zenoh implementation/header | `173168b42fc55b3ad1fca40857193c06bcb6b9afb7fc044ed46f677dd3ebf661` / `f31bd886b557b3e21e5af7299484dc6687f1efcb7f847676e77c2aa1bb84dce5` |

The source paths and commit are publicly addressable through the existing M0/SD-0001 evidence. This
document records hashes and summaries rather than source excerpts.

## Observed public contract projection

| Area | Revision-pinned observation | Contract consequence |
|---|---|---|
| Mapping cardinality | The selected mapping declares four Zenoh→SOME/IP routes and two SOME/IP→Zenoh routes, each with key, service, instance, event-group, and event identities. No exact identity is reproduced here. | The compatibility contract may expose direction/count and field shape; exact values remain restricted. |
| Zenoh session | The gateway constructs one client session and connects to one endpoint compiled into the source/binary. The endpoint is within a private address range and is not supplied by either selected JSON file. | The exact artifact cannot be treated as environment-neutral. The owner must approve that endpoint inside the pinned boundary or authorize a reproducible configurable rebuild. |
| Zenoh messaging | It declares subscribers for configured ingress keys, publishes reverse payload bytes, and marks its own publications to suppress echo. | Session/discovery/delivery guarantees and peer version remain unverified. |
| SOME/IP discovery | The selected configuration enables service discovery over UDP. | Multicast/address/port values remain restricted; network allow/deny policy is unresolved. |
| SOME/IP service transport | One configured service contains both reliable and unreliable endpoint declarations. The selected event request/offer operations explicitly use unreliable reliability. | The public contract can identify unreliable event delivery; retry, loss, ordering, and duplicate semantics remain unverified. |
| SOME/IP library | The bundle contains vsomeip files named as version 3.6.1 with SONAME major 3. | Pin 3.6.1 for the candidate bundle; exact wire/API compatibility with peers remains unverified. |
| Zenoh library | The bundled library is pinned by SHA-256 `49bfc1572a8b35b77050a91334fbc73024e798865a834e364e6544ff3f870187` and SONAME `libzenohc.so`; no trustworthy semantic version metadata was found. | Use the binary digest as artifact identity and keep the Zenoh version unknown. |
| Working directory | Source loads both selected JSON files through relative paths; the candidate plan supplies the matching immutable bundle working directory. | Changing the working directory is incompatible with this artifact. |
| Runtime libraries | The executable requires the bundled Zenoh/vsomeip libraries plus unbundled system C/C++ runtime libraries. | Environment pinning remains mandatory. |

## Observed selected-route transformations

| Direction | Selected route count | Source-observed transformation |
|---|---:|---|
| Zenoh→SOME/IP | 1 | Accept text-form or native-memory float32; emit native-memory float32 after a unit-scale conversion. |
| Zenoh→SOME/IP | 1 | Accept text-form or native-memory float32; emit native-memory float32 without a declared unit conversion. |
| Zenoh→SOME/IP | 1 | Accept text-form or native-memory float32; suppress repeated nonzero values and emit a delayed zero reset pulse after 100 ms using a detached worker. |
| Zenoh→SOME/IP | 1 | Accept several textual boolean spellings; emit one byte with zero/nonzero meaning. |
| SOME/IP→Zenoh | 2 | Forward received payload bytes unchanged. Source-side interpretation is used for logging and does not define a converted Zenoh payload. |

The float paths use host-native in-memory representation and do not declare byte order, alignment,
schema version, finite range beyond parser checks, or peer ABI. These are source facts, not a portable
wire contract. Units are established for only the explicitly scaled path; exact signal identities and
other semantics remain restricted/unverified.

## Lifecycle and observation findings

- Initialization can report failure, but no externally typed readiness endpoint or probe exists.
  Service-availability callbacks and startup log messages are internal observations, not proof of both
  directions or the selected message path.
- The main process remains alive through a periodic loop and defines no signal handler. The router and
  delayed-reset work use detached threads, and the router exposes no stop operation. A process signal
  may terminate the program, but bounded graceful shutdown and outstanding-work disposition are not
  established.
- Source logging can include route identifiers, payload text/values, service/event identities, and
  errors. Raw output must be discarded or handled as restricted evidence and cannot be copied directly
  into repository evidence. The generic prototype process provider currently redirects child output
  to a null sink; a future target provider needs an explicit reviewed choice.
- Source includes standalone Zenoh and SOME/IP test-tool targets, but those executables are absent from
  the selected candidate bundle. They are neither approved external peers nor an available readiness
  probe for this artifact.
- No source-observed automatic retry, backpressure limit, queue bound, delivery acknowledgement, or
  overload policy establishes predictable failure behavior.

## Classified findings

| ID | Severity | Finding | Required disposition | Status |
|---|---|---|---|---|
| IA-R01 | BLOCKER | A private Zenoh endpoint is compiled into the selected gateway and lies outside both selected JSON configurations. | Owner accepts the exact endpoint within the pinned isolated network, or authorizes a reproducible rebuild that makes it an explicit reviewed input. | Open |
| IA-R02 | MAJOR | Selected float paths use native-memory representation without byte-order/ABI/schema declaration. | Approve a peer-specific ABI contract or a versioned portable serialization and rebuild; verify with bounded interoperability evidence. | Open |
| IA-R03 | MAJOR | Detached work, absent router stop, and absent signal handling leave graceful shutdown and outstanding-message disposition undefined. | Approve a process-level termination policy and prove bounded containment; source changes require separate legacy authorization or an external wrapper limitation. | Open |
| IA-R04 | MAJOR | Runtime logs may contain restricted identifiers and payload data. | Approve discard or restricted retention for raw output and produce only redacted structured public evidence. | Open |
| IA-R05 | MAJOR | Internal availability/log signals do not prove bidirectional interface readiness. | Define an external peer/message probe and expected outcomes before execution. | Open |
| IA-R06 | MINOR | The Zenoh library is digest-pinned but its semantic version is unavailable. | Obtain trustworthy provenance/version metadata or retain digest-only compatibility limits. | Open |
| IA-R07 | MINOR | Source test tools are not part of the candidate artifact. | Pin separate approved peer artifacts or include reproducibly built tools in a newly reviewed bundle. | Open |

## Gate effect

This audit strengthens SD-R03–SD-R05, SD-R06, and SD-R08. It supplies enough static detail to draft a
public target-specific interface projection, but runtime interoperability and owner acceptance remain
absent. The interface blocker, environment blocker, readiness blocker, retention blocker, resource
limit blocker, owner blocker, and vendor-disposition blocker all remain in the candidate plan.
