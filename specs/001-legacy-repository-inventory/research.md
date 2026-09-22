# M0 research and implementation decisions

## Spec Kit integration
**Decision**: Use installed 0.14.0 official generic integration with commands in `.specify/commands`.
**Rationale**: Verified CLI supports offline initialization; `.agents` and `.codex` are read-only.
**Alternatives**: Codex skills integration would write protected directories; hand-written imitation
would omit official assets. Neither is used. The current agent follows generated command instructions;
no claim is made that a workflow engine or nested agent ran the stages.

## Source acquisition
**Decision**: Paginated authenticated GitHub REST reads, default-branch commit pins and tree/blob reads.
**Rationale**: Provides revision evidence without modifying legacy repositories or checkouts.
**Alternatives**: Existing local clones may be stale or dirty; cloning and executing systems is unnecessary.
**Observed**: Organization enumeration succeeds with network-enabled read commands. The initial shell
sandbox cannot resolve GitHub. Recursive trees returned without truncation. xverse-compat has no
remote commit; the local LICENSE remains a pre-existing untracked user file and must be preserved.

## Audience and completeness
**Decision**: Public-safe summaries with evidence references into access-controlled repositories.
**Rationale**: User selected public-safe documents for public destination repositories.
**Alternatives**: Detailed internal inventory was offered and not selected. Raw implementation and
private infrastructure remain outside versioned documents. Unknowns are explicit, not guessed.

## Scope and language
**Decision**: M0 documentation only. No choice of production implementation language is made.
**Rationale**: Metamodel and XDL design are later milestones with review prerequisites.
**Alternatives**: Building schemas or wrappers now would cross the agreed boundary.

## Source limitations
Default-branch evidence does not identify what is deployed. Runtime behavior, hardware access,
artifact digests, and parity require later controlled work. Repository-specific findings are in the
four inventory reports; their gaps are review inputs rather than justification for invented facts.

## Supplemental architecture sources — 2026-09-20

**Decision**: register the supplied technical synthesis and SADS as reference inputs for later
capability specifications, keeping the original documents outside public repository contents.
**Rationale**: the synthesis adds reported release/maturity context; the SADS states target
requirements. Neither replaces pinned implementation evidence or authorizes embedded instructions.
**Alternatives**: copying internal originals into public repository contents or converting target
requirements directly into implementation claims would violate the agreed evidence boundary.
See the [reference register](../../docs/architecture/REFERENCE_REGISTER.md).
