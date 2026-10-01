import os
import tempfile

# Must be set before the app is imported.
_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db}")  # CI/Postgres can pre-set it

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture(scope="session")
def client():
    seed(reset=True)
    with TestClient(app) as c:
        yield c


def login(client, email, role=None, password="demo1234"):
    body = {"email": email, "password": password}
    if role:
        body["role"] = role
    r = client.post("/api/auth/login", json=body)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="session")
def patient(client):
    return login(client, "patient@demo.com", "patient")


@pytest.fixture(scope="session")
def staff(client):
    return login(client, "staff@demo.com", "hospital")


@pytest.fixture(scope="session")
def amb(client):
    return login(client, "ambulance@demo.com", "ambulance")


@pytest.fixture(scope="session")
def admin(client):
    return login(client, "admin@demo.com", "admin")
