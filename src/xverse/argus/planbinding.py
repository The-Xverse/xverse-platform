"""XDL plan binding through the accepted public digest API.

Argus does not reimplement or reparse plan identity: it calls the accepted
``xverse_xdl.experiment_plan.plan_matches_digest`` public function (read at call time) and records
the verified semantic digest separately from caller-declared source-byte provenance
(``detailed-design.md`` section 7, invariant ``ARGUS2-INV-02``).
"""

from __future__ import annotations

from typing import Any

from xverse_xdl import experiment_plan as _experiment_plan

from .diagnostics import EvidenceDiagnostic, diagnostic

__all__ = ["envelope_run_id", "plan_identity"]


def _plan_api_version(plan: dict[str, Any]) -> str | None:
    selection = plan.get("selection")
    if isinstance(selection, dict):
        system = selection.get("system")
        if isinstance(system, dict) and isinstance(system.get("apiVersion"), str):
            return system["apiVersion"]
    profile = plan.get("profile")
    if isinstance(profile, dict):
        resource = profile.get("resource")
        if isinstance(resource, dict) and isinstance(resource.get("apiVersion"), str):
            return resource["apiVersion"]
    return None


def _plan_profile_version(plan: dict[str, Any]) -> str | None:
    profile = plan.get("profile")
    if isinstance(profile, dict):
        resource = profile.get("resource")
        if isinstance(resource, dict) and isinstance(resource.get("version"), str):
            return resource["version"]
    return None


def plan_identity(plan: Any) -> tuple[dict[str, Any] | None, list[EvidenceDiagnostic]]:
    """Verify and return the frozen manifest ``plan`` block, or stable rejection diagnostics."""

    if not isinstance(plan, dict):
        return None, [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "an accepted resolved plan object is required",
                pointer="/plan",
                remediation="Supply the accepted resolved experiment plan.",
            )
        ]

    api_version = _plan_api_version(plan)
    plan_version = plan.get("planVersion")
    if api_version != _experiment_plan.API_VERSION or plan_version != _experiment_plan.PLAN_VERSION:
        return None, [
            diagnostic(
                "ARGUS2-PLAN-VERSION-UNSUPPORTED",
                "plan apiVersion/planVersion is outside the accepted XDL v1alpha1/plan '1' contract",
                pointer="/plan",
                remediation="Supply a plan from the accepted XDL compiler; versions are never coerced.",
            )
        ]

    digest = plan.get("digest")
    if not isinstance(digest, dict) or digest.get("algorithm") != "sha256" or not isinstance(digest.get("value"), str):
        return None, [
            diagnostic(
                "ARGUS2-PLAN-DIGEST-MISMATCH",
                "plan carries no accepted sha256 semantic digest",
                pointer="/plan/digest",
                remediation="Supply the digest recorded by the accepted compiler.",
            )
        ]

    # The decision is taken through the accepted public API, never a private reimplementation.
    if _experiment_plan.plan_matches_digest(plan) is not True:
        return None, [
            diagnostic(
                "ARGUS2-PLAN-DIGEST-MISMATCH",
                "recorded plan digest does not match the recomputed body digest",
                pointer="/plan/digest",
                remediation="Recompile the plan; the semantic digest is never repaired.",
            )
        ]

    block = {
        "apiVersion": api_version,
        "profileVersion": _plan_profile_version(plan),
        "planVersion": plan_version,
        "semanticDigest": {"algorithm": "sha256", "value": digest["value"]},
    }
    return block, []


def envelope_run_id(run_envelope: Any) -> str | None:
    """Return the declared envelope run identity, if any."""

    if isinstance(run_envelope, dict):
        value = run_envelope.get("runId")
        if isinstance(value, str):
            return value
    return None
