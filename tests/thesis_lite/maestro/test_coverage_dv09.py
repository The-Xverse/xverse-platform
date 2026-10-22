"""DV09 coverage-assessor controls (increment19, finding 422).

Single-record deletions, a duplicated broker generation record, the design row
generic-complete-missing-ready on an actually closed Argus run, and an explicit row-by-row
comparison of the pre-closure provisional report with the closed recomputation. Expected outcomes
follow ML-DESIGN-2026-10-03-v2 coverage-expected-tables.json; nothing is computed from coverage.py.
"""

import hashlib

from xverse.argus import EvidenceStore
from xverse.maestro.coverage import CoverageError, assess_preclosure, verify_closed

from .test_coverage import VALIDATOR, Fixture, row


def without(args, action, unit):
    kept = [e for e in args["annotations"] if not (e["extensions"]["xverse.maestro"]["action"] == action
                                                   and e["extensions"]["xverse.maestro"]["unitId"] == unit)]
    assert len(kept) == len(args["annotations"]) - 1
    args["annotations"] = kept
    return args


def ids(report):
    return [r["obligationId"] for r in report["rows"]]


def test_dropping_only_the_ready_record_leaves_ready_missing(tmp_path):
    f = Fixture(tmp_path)
    original = f.provisional().report()
    changed = assess_preclosure(f.admission, **without(f.arguments(), "ready", f.a)).report()
    VALIDATOR.validate(changed)
    assert ids(changed) == ids(original)
    assert row(changed, "ready", f.a, 1)["status"] == "missing"
    assert changed["normalRecordStatus"] == "incomplete" and changed["overallStatus"] == "incomplete"
    f.writer.abort(reason="Synthetic ready deletion control")


def test_dropping_only_the_intent_record_never_completes(tmp_path):
    f = Fixture(tmp_path)
    original = f.provisional().report()
    changed = assess_preclosure(f.admission, **without(f.arguments(), "intent", f.a)).report()
    VALIDATOR.validate(changed)
    assert ids(changed) == ids(original)
    intent = row(changed, "intent", f.a, 1)
    print("E2", intent["status"], changed["normalRecordStatus"], changed["overallStatus"])
    assert intent["status"] != "satisfied"
    assert changed["normalRecordStatus"] != "complete"
    assert changed["overallStatus"] in ("incomplete", "unverifiable")
    f.writer.abort(reason="Synthetic intent deletion control")


def test_duplicated_broker_generation_record_never_completes(tmp_path):
    f = Fixture(tmp_path)
    args = f.arguments()
    generations = args["broker"]["generations"]
    first = next(g for g in generations if g["unitId"] == f.a and g["generation"] == 1)
    generations.append(dict(first))
    try:
        report = assess_preclosure(f.admission, **args).report()
    except CoverageError as error:
        print("E3 CoverageError", error)
    else:
        print("E3 report", report["normalRecordStatus"], report["overallStatus"])
        assert report["normalRecordStatus"] != "complete" and report["overallStatus"] != "complete"
    f.writer.abort(reason="Synthetic duplicate generation control")


def test_generic_argus_complete_never_promotes_missing_lifecycle_ready(tmp_path, monkeypatch):
    emit = Fixture.emit
    skipped = []

    def no_ready_for_first_unit(self, action, unit, *args, **kwargs):
        if action == "ready" and unit == self.units[0].unit_id:
            skipped.append(unit)
            return "skipped-ready"
        return emit(self, action, unit, *args, **kwargs)

    monkeypatch.setattr(Fixture, "emit", no_ready_for_first_unit)
    f = Fixture(tmp_path)
    monkeypatch.setattr(Fixture, "emit", emit)
    assert skipped == [f.a]
    f.close()
    reader = EvidenceStore.read_run(f.root)
    assert reader.assessed_evidence_status == "complete" and not reader.diagnostics
    result = verify_closed(f.admission, f.root, expected_admission_digest=f.admission.digest)
    report = result.coverage.report()
    VALIDATOR.validate(report)
    assert result.writer_state == "closed" and result.accepted_reader_executed
    assert row(report, "ready", f.a, 1)["status"] == "missing"
    assert report["normalRecordStatus"] == "incomplete" and report["overallStatus"] == "incomplete"


def test_provisional_and_closed_rows_agree_one_by_one(tmp_path):
    f = Fixture(tmp_path)
    provisional = f.close().report()
    closed = verify_closed(f.admission, f.root, expected_admission_digest=f.admission.digest).coverage.report()
    key = lambda report: [(r["obligationId"], r["unitId"], r["generation"], r["status"]) for r in report["rows"]]
    # The report's own artifact exists only after publication and indexing (finding 423).
    own = "ob.artifact." + hashlib.sha256(f.ad["reportPath"].encode()).hexdigest()
    assert [k for k in key(closed) if k[0] != own] == key(provisional)
    assert [k for k in key(closed) if k[0] == own] == [(own, None, 0, "satisfied")]
    assert provisional["normalRecordStatus"] == closed["normalRecordStatus"] == "complete"
    assert provisional["overallStatus"] == "incomplete" and provisional["assessmentStage"] == "pre-closure"
    assert closed["overallStatus"] == "complete"
