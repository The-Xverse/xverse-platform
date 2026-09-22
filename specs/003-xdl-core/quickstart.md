# Validate and review M2

Run from \`xverse-platform\`:

\`\`\`sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
python3 scripts/validate_m2.py --self-test
python3 scripts/validate_m2.py
git diff --check
\`\`\`

Expected: the feature resolves to \`specs/003-xdl-core\`; all JSON schemas parse, five YAML examples
parse and pass bounded semantic checks, schema references resolve, negative fixtures are rejected,
and no unresolved placeholders or forbidden runtime artifacts appear.

## Human review

1. Review [the feature specification](spec.md) and clarification decisions.
2. Review the normative [XDL Core v0.1 specification](../../xdl/specification/XDL_CORE_V0_1.md).
3. Compare the five schemas to the resource and normalized-model documentation.
4. Inspect each YAML example as illustrative data, not an executable blueprint.
5. Review ADR-0009 through ADR-0012 and the separate M2 architecture review.
6. Complete [the M2 acceptance checklist](checklists/acceptance.md) before authorizing a loader,
   validator library, runtime-plan compiler, catalog, adapter, or M3 capability.

## Negative scenarios

Validation must reject an unsupported API version/kind, unknown core field, duplicate element ID,
unresolved local reference, undeclared extension namespace, realization field in System, incomplete
Deployment readiness contract, and malformed Profile namespace. These checks demonstrate specification
consistency only; they are not production parser certification.

