import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

test_state = tempfile.TemporaryDirectory(prefix="salus-tests-")
os.environ["SALUS_STATE_DIR"] = str(Path(test_state.name))

from app.main import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as running:
        yield running
