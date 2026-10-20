"""Pure original output/budget admission; no directory discovery or workload authority."""
from dataclasses import asdict, dataclass
import os

from .artifacts import ArtifactDeclaration, CollectionError
from .coverage import CoverageAdmission, _number, canonical


@dataclass(frozen=True)
class CollectionPlan:
    coverage_digest: str
    source_root: str
    source_identity: tuple[int, int]
    declarations: tuple[ArtifactDeclaration, ...]
    byte_limits: tuple[int, ...]
    metadata_path: str
    metadata_maximum_bytes: int
    operation_seconds: float
    per_unit_teardown_seconds: float
    collection_seconds: float
    terminal_seconds: float
    drain_seconds: float
    terminal_reserve_seconds: float

    def configuration(self):
        return asdict(self)

    @property
    def canonical_bytes(self):
        return canonical(self.configuration())

    @property
    def additional_requests(self):
        # Context, each item, metadata completion, coverage report, writer closure.
        return len(self.declarations) + 4


def admit_collection(coverage, *, expected_digest, source_root, source_identity,
                     declarations, metadata_path, operation_seconds,
                     per_unit_teardown_seconds, collection_seconds, terminal_seconds,
                     drain_seconds):
    if type(coverage) is not CoverageAdmission:
        raise CollectionError('ML-COLLECTION-COVERAGE')
    ad = coverage.data(expected_digest)
    if (type(source_root) is not str or not os.path.isabs(source_root)
        or any(part in ('.', '..') for part in source_root.split('/'))
        or '\x00' in source_root or len(source_root.encode()) > 4096
        or type(source_identity) is not tuple or len(source_identity) != 2
        or any(type(value) is not int or value < 0 for value in source_identity)):
        raise CollectionError('ML-COLLECTION-SOURCE-IDENTITY')
    if (type(declarations) not in (list, tuple) or len(declarations) > 128
        or any(type(d) is not ArtifactDeclaration for d in declarations)):
        raise CollectionError('ML-COLLECTION-DECLARATION')
    declarations = tuple(declarations)
    for d in declarations:
        d.__post_init__()
    units = {d.unit_id for d in declarations}
    if (len(units) > 16 or any(sum(d.unit_id == u for d in declarations) > 8 for u in units)
        or len({d.destination for d in declarations}) != len(declarations)
        or len({(d.unit_id, d.generation, d.source) for d in declarations}) != len(declarations)):
        raise CollectionError('ML-COLLECTION-COUNT')
    expected = {row['path']: row for row in ad['artifacts'] if row['unitId'] is not None}
    if set(expected) != {d.destination for d in declarations}:
        raise CollectionError('ML-COLLECTION-OUTPUT-UNIVERSE')
    caps = []
    for d in declarations:
        row = expected[d.destination]
        if (d.unit_id != row['unitId'] or d.generation != row['generation']
            or d.required is not row['required'] or row['maximumBytes'] > 1 << 20):
            raise CollectionError('ML-COLLECTION-OUTPUT-UNIVERSE')
        caps.append(row['maximumBytes'])
    if sum(caps) > 16 << 20:
        raise CollectionError('ML-COLLECTION-BYTE-LIMITS')
    internal = {ad[key] for key in ('brokerPath', 'retainedPath', 'reportPath')}
    metadata = next((r for r in ad['artifacts'] if r['path'] == metadata_path), None)
    if (type(metadata_path) is not str or metadata_path in internal
        or metadata is None or metadata['unitId'] is not None or metadata['generation'] != 0
        or metadata['required'] is not True or metadata['maximumBytes'] > 1 << 20
        or internal & set(expected)):
        raise CollectionError('ML-COLLECTION-METADATA')
    budgets = (operation_seconds, per_unit_teardown_seconds, collection_seconds,
               terminal_seconds, drain_seconds)
    if any(not _number(value) or not 0 < value <= maximum
           for value, maximum in zip(budgets, (5, 5, 10, 2, 2))):
        raise CollectionError('ML-COLLECTION-BUDGET')
    reserve = len(ad['units']) * per_unit_teardown_seconds + collection_seconds + terminal_seconds + drain_seconds
    return CollectionPlan(expected_digest, source_root, source_identity, declarations,
                          tuple(caps), metadata_path, metadata['maximumBytes'],
                          *budgets, reserve)


def decode_collection(value, coverage, expected_digest):
    fields = set(CollectionPlan.__dataclass_fields__)
    if (type(value) is not dict or set(value) != fields
        or type(value['declarations']) is not list or len(value['declarations']) > 128
        or type(value['source_identity']) is not list):
        raise CollectionError('ML-COLLECTION-CONFIG')
    declarations = []
    for row in value['declarations']:
        if type(row) is not dict or set(row) != set(ArtifactDeclaration.__dataclass_fields__):
            raise CollectionError('ML-COLLECTION-CONFIG')
        declarations.append(ArtifactDeclaration(**row))
    expected = admit_collection(coverage, expected_digest=expected_digest,
        source_root=value['source_root'], source_identity=tuple(value['source_identity']),
        declarations=declarations, metadata_path=value['metadata_path'],
        **{key: value[key] for key in ('operation_seconds', 'per_unit_teardown_seconds',
             'collection_seconds', 'terminal_seconds', 'drain_seconds')})
    if canonical(value) != expected.canonical_bytes:
        raise CollectionError('ML-COLLECTION-CONFIG')
    return expected


def bind_collection(plan, coverage, expected_digest, *, generation_ns, schedule, exports):
    """Rederive sealed input, original end and capacity before any runtime effects."""
    if type(plan) is not CollectionPlan:
        raise CollectionError('ML-COLLECTION-CONFIG')
    # Canonical JSON normalizes tuples only; it cannot change integer/bool types.
    import json
    expected = decode_collection(json.loads(plan.canonical_bytes), coverage, expected_digest)
    ad = coverage.data(expected_digest)
    if ad['end'] + expected.terminal_reserve_seconds > generation_ns / 1e9:
        raise CollectionError('ML-COLLECTION-RESERVE')
    requests = (schedule.required_requests if schedule is not None else 1) + len(exports) + 1
    limit = schedule.request_limit if schedule is not None else 128
    if (requests + expected.additional_requests > limit
        or schedule is not None and schedule.required_events + 2 > schedule.event_limit):
        raise CollectionError('ML-COLLECTION-CAPACITY')
    destinations = {d.destination for d in expected.declarations} | {expected.metadata_path}
    if destinations & {e.relative_path for e in exports}:
        raise CollectionError('ML-COLLECTION-EXPORT-CONFLICT')
    return expected
