import json,time,sys
from pathlib import Path
import pytest
from xverse.maestro.teardown import ReverseTeardown
from xverse.maestro.run_broker import RunUnitIssuer
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.time import HostDeadline
observations=[]
def observe(cls,name):
 original=getattr(cls,name)
 def measured(self,*args,**kw):
  began=time.monotonic();diagnostic=None
  try:return original(self,*args,**kw)
  except Exception as error:
   diagnostic=dict(type=type(error).__name__,code=str(error) if str(error).startswith('ML-') else None,errno=getattr(error,'errno',None));raise
  finally:
   deadlines=[v.monotonic_seconds for v in args if type(v) is HostDeadline]
   observations.append(dict(method=cls.__name__+'.'+name,began=began,ended=time.monotonic(),deadline=deadlines[-1] if deadlines else None,diagnostic=diagnostic))
 setattr(cls,name,measured)
for cls,name in [(ReverseTeardown,'_record'),(ReverseTeardown,'_cleanup'),(RunUnitIssuer,'retire_owned'),(PersistenceClient,'_rpc')]:observe(cls,name)
try:status=pytest.main(sys.argv[2:])
finally:Path(sys.argv[1]).write_text(json.dumps(observations,indent=2)+'\n')
raise SystemExit(status)
