# Validate and review M1

## Prerequisites

Run from \`xverse-platform\`. Bash and Python 3 are sufficient. No network access, legacy checkout,
container, simulator, device, or production process is required or permitted.

\`\`\`sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
python3 scripts/validate_m1.py --self-test
git diff --check
\`\`\`

Expected result: prerequisites resolve
\`specs/002-domain-neutral-metamodel\`; validation reports all 26 concepts, four ADRs, and no errors.

## Review procedure

1. Read [spec.md](spec.md) and [clarifications.md](clarifications.md) to verify scope and defaults.
2. Read [METAMODEL.md](../../docs/architecture/METAMODEL.md) and the
   [conceptual diagram](../../docs/architecture/METAMODEL_DIAGRAM.md).
3. Check each required concept has purpose, identity/lifecycle, required/optional attributes,
   relationships, validation, and extension treatment.
4. Check [ADRs 0005–0008](../../docs/adr/) for review status and consistency with the model.
5. Use [acceptance.md](checklists/acceptance.md) and the separate architecture review to record the
   human decision. Approval is required before M2 uses the proposed vocabulary.
6. Confirm no M1 file creates an XDL schema, runtime, adapter, legacy change, private source excerpt,
   credential, or sensitive deployment detail.

## Negative scenarios

The validator must reject a missing required concept, a core concept that lacks definition fields,
an unresolved template marker, an absent ADR, a broken local link, an implementation-status claim, or
a forbidden XDL/runtime artifact under the M1 feature. A reviewer must reject a profile that redefines
core identity/validation or an architecture claim that upgrades documented targets to demonstrated
runtime behavior.
