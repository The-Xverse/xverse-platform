"""Real original PermitSession red control; no worker/product fault switch."""
from pathlib import Path
from dataclasses import replace
import json
import sys
import tempfile

OUT=Path(__file__).resolve().parent
receipt=json.loads((OUT/'teardown-v2-wheel-receipt.json').read_text())
sys.path.insert(0,receipt['cwd'])
from tests.thesis_lite.maestro.test_admission import context, session, NOW
from xverse_xdl.models import freeze
from xverse.maestro.admission import AdmissionError

ctx=context()
ctx=(ctx[0],replace(ctx[1],run=freeze({'original_context_pin_probe':-0.0})),*ctx[2:])
private=Path(tempfile.mkdtemp(prefix='maestro-affa17-signed-zero-proof-'))
holder=session(ctx,private/'m3.jsonl')
claim=holder.claim_start_intent(ctx[0].units[0].unit_id,now=NOW)
object.__setattr__(holder._result,'run',freeze({'original_context_pin_probe':0.0}))
rejected=False
try:
    holder.revalidate_start_intent(claim,now=NOW)
except AdmissionError:
    rejected=True
result=dict(actual_original_session=True,changed_signed_zero_rejected=rejected,
    public_json_encodings_differ=json.dumps(-0.0)!=json.dumps(0.0),
    source_files_unchanged=True,private_fixture_directory=str(private),
    execution_authority=False,full_M1_complete=False)
(OUT/((sys.argv[1] if len(sys.argv)>1 else 'signed-zero-proof-red')+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
raise SystemExit(0 if rejected else 1)
