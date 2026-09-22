# M2 clarification record

**Feature**: [M2 XDL Core v0.1](spec.md)
**Date**: 2026-09-20
**Method**: Spec Kit ambiguity scan using approved M1 decisions, architecture guidance, and current
serialization standards.

| ID | Area | Decision | Effect |
|---|---|---|---|
| C01 | Resource packaging | Use separate System, Component, Deployment, Scenario, and Profile resources. | Preserves independent ownership/versioning and the M1 logical-realization-experiment split. |
| C02 | Identity | Use structured metadata and references; render canonical identity as \`xdl://namespace/kind/name#element\`. | Avoids path parsing and provider-local identity. |
| C03 | Serialization | Use the JSON data model, YAML 1.2.2 or JSON syntax, and JSON Schema Draft 2020-12. | Keeps one semantic model and mature validation tooling; no custom grammar. |
| C04 | Unknown fields | Reject unknown core fields; permit only declared, namespaced payloads under \`extensions\`. | Prevents silent typos and semantic drift while keeping explicit extensibility. |
| C05 | Versioning | Separate API/schema version, resource revision, profile version, and artifact/model version. | Prevents unrelated compatibility claims from being inferred from one number. |
| C06 | Compatibility | Require exact v1alpha1 recognition; breaking changes need a new API version and explicit conversion. | Alpha status is honest and does not promise silent forward compatibility. |
| C07 | Validation | Specify six validation gates; provide structural schemas and documentary validator now. | Maintains testability without implementing the later runtime loader/validator. |

No unresolved clarification marker remains. Concrete conversion algorithms, bundle/import behavior,
registry hosting, loaders, runtime plans, adapters, and provider profiles are deferred.

