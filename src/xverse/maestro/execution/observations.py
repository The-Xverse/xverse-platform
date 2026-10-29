"""Bounded original native batches from trusted installed providers, never HTTP."""
from dataclasses import dataclass, field
import json

from .inspection import ExecutionInputError, _ID, canonical, sha256


@dataclass(frozen=True)
class NativeObservationBatch:
    """Original source sequence is distinct from native per-message sequence."""
    provider_id: str
    sequence: int
    projection_bytes: bytes = field(repr=False)

    def __post_init__(self):
        if (type(self.provider_id) is not str or not _ID.fullmatch(self.provider_id)
                or type(self.sequence) is not int or not 1 <= self.sequence < 2**63
                or type(self.projection_bytes) is not bytes
                or not 1 <= len(self.projection_bytes) <= 65536):
            raise ExecutionInputError('MPX-NATIVE-BATCH-INVALID')
        self.to_data()

    @property
    def digest(self):
        return sha256(self.projection_bytes)

    def to_data(self):
        try:
            value = json.loads(self.projection_bytes)
            if (type(value) is not dict or type(value.get('records')) is not list
                    or not 1 <= len(value['records']) <= 32):
                raise ValueError()
            canonical(value)
            return value
        except (ValueError, TypeError, RecursionError):
            raise ExecutionInputError('MPX-NATIVE-BATCH-INVALID') from None

    def validate_identity(self, prepared, binding):
        value = self.to_data()
        extensions = value.get('extensions')
        witness = extensions.get('io.xverse.maestro.execution') if type(extensions) is dict else None
        expected = {'runId': prepared.submission.run_id,
            'planDigest': prepared.submission.expected_plan_digest,
            'inputSemanticDigest': prepared.submission.expected_input_semantic_digest,
            'providerId': binding.provider_id,
            'installationDigest': binding.configuration.installation_digest,
            'batchSequence': self.sequence}
        if (self.provider_id != binding.provider_id or type(witness) is not dict
                or any(type(witness.get(k)) is not type(v) or witness.get(k) != v for k, v in expected.items())):
            raise ExecutionInputError('MPX-NATIVE-SOURCE-MISMATCH')
        # The original compiler flow IDs are canonical within the pinned System.
        system = prepared.submission.selection.system_ref
        flows = prepared.inspection.to_data()['plan']['flows']
        routes = {system + '#' + f['id']: {system + '#' + f['sourceEndpointId'],
            *(system + '#' + endpoint for endpoint in f['destinationEndpointIds'])} for f in flows}
        interfaces = {system + '#' + f['id']: system + '#' + f['interfaceId'] for f in flows}
        for record in value['records']:
            if (type(record) is not dict or record.get('providerId') != binding.provider_id
                    or type(record.get('routeId')) is not str
                    or record.get('routeId') not in routes
                    or type(record.get('endpointId')) is not str
                    or record.get('endpointId') not in routes[record['routeId']]
                    or record.get('interfaceId') != interfaces[record['routeId']]):
                raise ExecutionInputError('MPX-NATIVE-ROUTE-MISMATCH')
        snapshots = extensions.get('io.xverse.native.snapshots', [])
        if type(snapshots) is not list or len(snapshots) > 8:
            raise ExecutionInputError('MPX-NATIVE-SNAPSHOT-INVALID')
        taps = {record.get('tapId') for record in value['records'] if type(record.get('tapId')) is str}
        if any(type(snapshot) is not dict or type(snapshot.get('declaredTapId')) is not str
               or snapshot['declaredTapId'] not in taps for snapshot in snapshots):
            raise ExecutionInputError('MPX-NATIVE-SNAPSHOT-INVALID')
        inputs = extensions.get('io.xverse.native.inputs', [])
        if type(inputs) is not list or len(inputs) > 32:
            raise ExecutionInputError('MPX-NATIVE-INPUT-INVALID')
        seen = set()
        for original in inputs:
            if (type(original) is not dict or original.get('schemaVersion') != '1.0'
                    or type(original.get('eventId')) is not str or not _ID.fullmatch(original['eventId'])
                    or original['eventId'] in seen
                    or original.get('producerId') != binding.provider_id + '.input'
                    or original.get('origin') not in ('configured-input', 'transport-ingress')
                    or type(original.get('routeId')) is not str or original['routeId'] not in routes
                    or type(original.get('endpointId')) is not str
                    or original['endpointId'] not in routes[original['routeId']]
                    or type(original.get('sourceClock')) is not dict
                    or type(original.get('correlationId')) is not str
                    or original.get('upstreamCausationId') is not None
                       and (type(original['upstreamCausationId']) is not str
                            or not _ID.fullmatch(original['upstreamCausationId']))):
                raise ExecutionInputError('MPX-NATIVE-INPUT-INVALID')
            seen.add(original['eventId'])
        return value
