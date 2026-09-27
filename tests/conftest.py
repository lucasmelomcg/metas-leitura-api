import os
import tempfile

import pytest

_DB_TEMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_TEMP.name}"
os.environ["API_KEY"] = "chave-de-teste"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app, headers={"X-API-Key": "chave-de-teste"}) as cliente:
        yield cliente
