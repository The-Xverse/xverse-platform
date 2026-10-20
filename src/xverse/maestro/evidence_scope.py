"""Pure original runtime assessment context; grants no control or time extension."""
from dataclasses import dataclass
import hashlib


def runtime_admission_digest(coverage,plan,generation_ns):
    from .coverage import canonical
    return 'sha256:'+hashlib.sha256(canonical(dict(coverageDigest=coverage.digest,
        collectionDigest='sha256:'+hashlib.sha256(plan.canonical_bytes).hexdigest(),
        generationNs=generation_ns))).hexdigest()


@dataclass(frozen=True)
class RuntimeEvidenceScope:
    collection_bytes: bytes
    generation_ns: int

    def validate(self,admission,external_digest,expected_runtime_digest):
        """Rederive original inputs against the caller's external pin, without I/O."""
        from .coverage import CoverageError,_json,_number
        from .collection_plan import decode_collection
        try:
            ad=admission.data(external_digest)
            if type(self.collection_bytes) is not bytes or type(self.generation_ns) is not int:
                raise CoverageError('ML-COVERAGE-RUNTIME-SCOPE')
            plan=decode_collection(_json(self.collection_bytes,1<<20),admission,external_digest)
            if (expected_runtime_digest is None
                or runtime_admission_digest(admission,plan,self.generation_ns)!=expected_runtime_digest
                or self.generation_ns < int((ad['end']+plan.terminal_reserve_seconds)*1e9)):
                raise CoverageError('ML-COVERAGE-RUNTIME-SCOPE')
            end=(self.generation_ns-int(plan.drain_seconds*1e9))/1e9
            if not _number(end) or end<ad['end']:
                raise CoverageError('ML-COVERAGE-RUNTIME-SCOPE')
            return end
        except (ValueError,TypeError,KeyError,OverflowError,AttributeError) as error:
            raise CoverageError('ML-COVERAGE-RUNTIME-SCOPE') from error
