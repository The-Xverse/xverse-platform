"""X-Verse Definition Language v1alpha1 reference loader."""

from .models import (
    Diagnostic,
    ElementIdentity,
    FrozenMap,
    LoadLimits,
    NormalizedResource,
    ResourceIdentity,
    ResolvedReference,
    Severity,
    SourceLocation,
    StaticReadiness,
    ValidationGate,
    ValidationResult,
)
from .loader import SourceInput

__version__ = "0.4.0"
SUPPORTED_API_VERSIONS = ("xverse.io/xdl/v1alpha1",)

# Added after module initialization to avoid import cycles in the staged implementation.
from .normalize import canonical_json  # noqa: E402
from .validate import validate_files, validate_sources  # noqa: E402
from .catalog import (  # noqa: E402
    RUNTIME_PROFILE_NAMESPACE, CatalogBuildResult, CatalogEntry, LifecyclePlan, PlanAction,
    ProcessAction, build_lifecycle_plan, catalog_entry_public_data, derive_catalog,
)
from .lifecycle import (  # noqa: E402
    EvidenceRecord, EvidenceWriteError, ExecutionPermit, FileEvidenceJournal, FixtureProvider,
    InMemoryEvidenceJournal, IsolationAttestation, LifecycleController, LifecycleDiagnostic,
    LifecycleError, LifecycleProvider, LifecycleResult, OwnedResourceHandle, ProcessProvider,
)

__all__ = [
    "SUPPORTED_API_VERSIONS", "CatalogBuildResult", "CatalogEntry", "Diagnostic", "ElementIdentity",
    "EvidenceRecord", "EvidenceWriteError", "ExecutionPermit", "FileEvidenceJournal", "FixtureProvider",
    "FrozenMap", "InMemoryEvidenceJournal", "IsolationAttestation", "LifecycleController",
    "LifecycleDiagnostic", "LifecycleError", "LifecyclePlan", "LifecycleProvider", "LifecycleResult", "LoadLimits",
    "NormalizedResource", "ResourceIdentity", "ResolvedReference", "Severity", "SourceInput", "SourceLocation",
    "OwnedResourceHandle", "PlanAction", "ProcessAction", "ProcessProvider", "RUNTIME_PROFILE_NAMESPACE",
    "StaticReadiness", "ValidationGate", "ValidationResult", "__version__", "build_lifecycle_plan",
    "canonical_json", "catalog_entry_public_data", "derive_catalog", "validate_files", "validate_sources",
]
