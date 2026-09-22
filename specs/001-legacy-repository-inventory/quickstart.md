# Validate and review M0

## Prerequisites
Use sibling checkouts named xverse-platform, xverse-compat, and xverse-blueprints. Bash and Python 3
are sufficient for offline checks. Spec Kit 0.14.0 is already initialized; GitHub access is needed
only to independently inspect private evidence or refresh the inventory.

## Run from xverse-platform
```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
python3 scripts/validate_m0.py --self-test
```
Expected: the prerequisite command resolves `specs/001-legacy-repository-inventory`; the validator
reports coverage and no errors. The actual Git branch can stay `main`: Spec Kit's feature pointer
selects the feature independently of branch creation.

Compare the original guidance with its architecture copy and the original LICENSE files with their
recorded hashes. Inspect `git status --short` and `git diff --check` in each vNext repository. Untracked
files must also be reviewed; a clean tracked diff alone is not proof of an empty change set.

## Review scenarios
1. Follow the README to the single M0 specification and all four legacy reports.
2. Select a repository; verify its 15 fields, commit pin, and source links. Private evidence may require login.
3. Follow cruise-control dependency edges back to startup source; distinguish launch requests from readiness.
4. Verify documentation-only repositories and unknown contracts are not represented as working components.
5. Check the architecture review and complete the human boundary/interface/dependency review before M1.

## Negative scenarios
The validator must reject missing repository entries, malformed revision pins, missing source paths,
and inconsistent guidance/constitution copies. API denial or empty repositories must remain explicit
coverage states; they must never be silently removed from a refreshed snapshot.

## Refresh procedure
Read the M0 Spec Kit instructions and retain the same scope. Enumerate all organization repositories
with paginated GET requests, resolve new pins, inspect sources, and update the four reports and
sanitized snapshot together. Keep raw private source outside repositories. Repeat offline checks and
the separate architecture review. Do not replace evidence pins with mutable branch links.
