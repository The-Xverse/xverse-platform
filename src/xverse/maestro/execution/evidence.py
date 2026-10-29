"""Original public-execution lifecycle decisions, persisted by actual Argus."""
import time
import uuid

from xverse.argus import EvidenceLimits, EvidenceStore
from .inspection import ExecutionInputError


class LifecycleEvidence:
    """One bounded writer; source clocks are host monotonic, not simulation time."""
    def __init__(self, root, prepared, *, clock_domain, source_clocks=None):
        self.sequence = 0
        self.clock_domain = clock_domain
        self.prepared = prepared
        self.writer = EvidenceStore.open_run(
            root, run_id=prepared.submission.run_id,
            plan=prepared.inspection.to_data()['plan'],
            limits=EvidenceLimits(max_event_bytes=16384, max_events=4096,
                max_read_records=4096, max_causal_index_entries=4096,
                max_manifest_bytes=1024*1024, max_artifacts=64),
            clocks={'host': self.clock(), **(source_clocks or {})},
        )

    def clock(self):
        return {'domain': self.clock_domain, 'unit': 'ns', 'value': time.monotonic_ns()}

    def append(self, *, operation_id, correlation_id, kind, phase=None,
               outcome=None, causation_id=None, readiness_kind=None, resources=(),
               observation=None):
        # Argus treats correlationId as an event reference. The original start
        # request owns this identity; no placeholder predecessor is synthesized.
        event_id = correlation_id if kind == 'run-start-requested' else 'mpx-' + uuid.uuid4().hex
        sequence = self.sequence + 1
        data = {'schemaVersion': '1.0', 'kind': kind, 'operationId': operation_id,
            'runId': self.prepared.submission.run_id,
            'planDigest': self.prepared.submission.expected_plan_digest,
            'inputSemanticDigest': self.prepared.submission.expected_input_semantic_digest,
            'preparationDigest': self.prepared.digest,
            'sourceDigests': self.prepared.inspection.to_data()['sourceDigests'],
            'phaseId': phase.phase_id if phase else None,
            'logicalId': phase.logical_id if phase else None,
            'providerId': phase.provider_id if phase else None,
            'operation': phase.operation if phase else None,
            'outcome': outcome, 'readinessKind': readiness_kind,
            'resources': list(resources), 'observation': observation}
        clock = self.clock()
        self.writer.append_event(event_id=event_id, producer_id='maestro-public-execution',
            producer_sequence=sequence, event_kind='annotation',
            correlation_id=None if kind == 'run-start-requested' else correlation_id,
            causation_id=causation_id,
            clocks={'host': clock}, extensions={'io.xverse.maestro.execution': data})
        self.writer.flush_buffer()
        self.sequence = sequence
        return event_id, clock

    def close(self, *, failed, reason=None):
        if failed:
            self.writer.abort(reason=reason or 'Maestro execution failed or cleanup is uncertain')
        else:
            self.writer.finalize()

    def import_observations(self, projection):
        """Actual Argus import; native original fields remain authoritative."""
        snapshots = projection.get('extensions', {}).get('io.xverse.native.snapshots', ())
        inputs = projection.get('extensions', {}).get('io.xverse.native.inputs', ())
        for record in projection.get('records', ()):
            for key in ('sourceClock', 'observationClock'):
                clock = record.get(key)
                if type(clock) is dict and clock.get('domain') not in self.writer.declared_domains:
                    raise ExecutionInputError('MPX-NATIVE-CLOCK-UNDECLARED')
        for snapshot in snapshots:
            interval = snapshot.get('intervalProvenance')
            if type(interval) is dict:
                for key in ('start', 'end'):
                    clock = interval.get(key)
                    if type(clock) is dict and clock.get('domain') not in self.writer.declared_domains:
                        raise ExecutionInputError('MPX-NATIVE-CLOCK-UNDECLARED')
        for original in inputs:
            if original['sourceClock'].get('domain') not in self.writer.declared_domains:
                raise ExecutionInputError('MPX-NATIVE-CLOCK-UNDECLARED')
        input_ordinals = []
        for original in inputs:
            input_ordinals.append(self.writer.append_event(event_id=original['eventId'],
                producer_id=original['producerId'], event_kind='annotation',
                correlation_id=original['correlationId'],
                causation_id=original.get('upstreamCausationId'),
                clocks={'source': original['sourceClock']},
                extensions={'io.xverse.native.input': original}))
        ordinals = self.writer.import_observation(projection)
        snapshot_ordinals = []
        for snapshot in snapshots:
            snapshot_ordinals.append(self.writer.import_snapshot(snapshot))
        self.writer.flush_buffer()
        return ordinals, tuple(snapshot_ordinals), tuple(input_ordinals)
