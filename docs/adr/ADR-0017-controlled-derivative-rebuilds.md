# ADR-0017: Controlled derivative rebuilds for legacy compatibility

**Status**: Accepted — strategy authorized by the user on 2026-09-21; target patch remains gated.

**Date**: 2026-09-21

## Context

The exact SD-0001 gateway artifact is reproducible in an isolated build but embeds environment-specific
data and has unresolved portability, lifecycle, logging, and readiness constraints. Accepting that
artifact as the vNext compatibility baseline would preserve those constraints. Editing its legacy
repository would violate the parallel-evolution and production-immutability decisions.

## Decision

`xverse-compat` owns a controlled derivative-rebuild mechanism. It consumes an exact frozen Git
revision/tree and a separately controlled digest-pinned patch, stages only committed source outside the
legacy checkout, builds twice in independent roots, and accepts a candidate only when declared output
digests match.

The public repository contains the mechanism, manifest/result contracts, tests, and public digest
evidence. Restricted patch contents and deployment values remain in an approved controlled store. The
mechanism constrains patch targets, commands, environment, and outputs; uses no shell or source-selected
tool; and emits no source excerpt, private value, build output, or environment value.

The first target patch may externalize the compiled endpoint, introduce an explicitly selected
serialization mode, make lifecycle termination bounded, eliminate detached work, and redact or route
logs according to an approved policy. It must preserve route mappings unless a separate decision
authorizes a mapping change.

## Consequences

A derivative receives a new artifact digest and cannot inherit the acceptance status of the original
artifact. Build reproducibility does not establish interface compatibility, readiness, parity, safety,
or production suitability. The SD-0001 owner, environment, interface, readiness, resource, retention,
and vendor-disposition blockers remain until direct evidence closes them.

The rebuild mechanism can be implemented and tested with controlled fixtures before the target patch
exists. Supplying the target patch requires a later human acceptance of the mechanism and restricted
decisions. Running any derivative remains subject to an exact platform execution permit.

## Scope

This ADR authorizes the repository boundary and reusable build mechanism. It does not publish or approve
a target patch, select peer ABI or deployment values, implement a target provider, execute a legacy or
derivative process, or change a legacy repository.
