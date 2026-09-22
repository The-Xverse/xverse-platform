# Contract: X-COM communication provider

A provider realizes routes without owning logical topology. Providers are explicitly composed; the
first capability performs no dynamic discovery or arbitrary library loading.

## Operations

- describe provider identity, contract version, capabilities, and hard limits;
- prepare one validated route plan without emitting traffic;
- activate endpoints and return opaque generation-bound handles;
- submit signal/message/service items with an explicit bounded outcome;
- observe provider and endpoint state without inferring health from time alone;
- drain and close only exact owned handles;
- reconcile persisted handles after controller/provider interruption.

## Required behavior

- reject unsupported semantics before activation;
- never strengthen delivery, ordering, timing, or fidelity claims;
- allocate bounded resources and expose saturation outcomes;
- make callbacks and handle lifetime/thread-safety explicit;
- do no ambient network discovery, shell execution, or legacy-repository access;
- preserve item provenance and correlation or report the exact declared loss;
- remain replaceable by another conforming provider.

The initial loopback provider is test evidence only. Passing its suite does not prove a network
provider, transport protocol, or legacy bridge compatible.

