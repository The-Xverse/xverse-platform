# M0 documentary record model

This describes inventory evidence, not the future platform metamodel or XDL.

- **Snapshot**: capture timestamp, organization, scope, repositories, and enumeration method.
- **Repository**: unique full name, role (legacy/vNext), default branch, visibility, archived/fork flags,
commit SHA or explicit empty/error status, tree coverage, inspected source paths, and inventory anchor.
- **Evidence**: repository identity, commit SHA, source path or tree, immutable GitHub URL, and observation
scope. Evidence from private repositories requires the reader's own access.
- **Inventory entry**: the 15 section-40 fields; classification, maturity, source-backed observations,
inferences, unknowns, and public-safe omissions. Unknown is a valid value, not a blank field.
- **Dependency**: source and target repository or external system, relationship type, evidence reference,
and confidence (observed configuration/source, documented, or inferred). Dependency does not imply
startup ordering, deployed use, or version compatibility.
- **Interface**: owner, direction, protocol, summarized inputs/outputs, configuration mechanism,
evidence, and unresolved contract details. No sensitive endpoint values are included.
- **Finding**: stable identifier, BLOCKER/MAJOR/MINOR/ADVISORY severity, affected milestone, evidence,
impact, and required disposition.

Validation: repository names are unique; all enumeration records are classified; commit pins are full
40-character SHAs when present; evidence paths occur in inspected trees; report references resolve.
Lifecycle: source snapshot → inspected summary → validated package → human review. The last state
requires actual reviewer decisions and is not set by automated checks.
