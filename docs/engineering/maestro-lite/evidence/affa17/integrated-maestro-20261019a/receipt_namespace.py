import os
from pathlib import Path
import pytest
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    root=Path(os.environ['MAESTRO_FULL_RECEIPT_ROOT'])
    target=root/item.path.stem
    target.mkdir(parents=True,exist_ok=True)
    os.environ['MAESTRO_BOUNDARY_RECEIPTS']=str(target)
