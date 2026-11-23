"""Milestone 1 checks: authentication, roles, patients, cases, upload validation and preprocessing.
Run from the milestone1_backend folder:  pytest -q
"""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["STORAGE_DIR"] = _tmp
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["LOGIN_RATE_LIMIT_PER_MIN"] = "1000"

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.ml.preprocessing import LoadedImage, preprocess  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def register(client, email, role):
    r = client.post("/api/auth/register", json={"email": email, "full_name": "Test User",
                                                "password": "Passw0rd!", "role": role})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def png(h=300, w=400):
    return cv2.imencode(".png", np.random.default_rng(0).integers(60, 200, (h, w), dtype=np.uint8))[1].tobytes()


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_registration_and_login_rules(client):
    weak = client.post("/api/auth/register", json={"email": "w@t.io", "full_name": "Weak", "password": "weak",
                                                   "role": "radiologist"})
    assert weak.status_code == 400
    admin = client.post("/api/auth/register", json={"email": "a@t.io", "full_name": "Admin", "password": "Passw0rd!",
                                                    "role": "admin"})
    assert admin.status_code == 422
    h = register(client, "doc@t.io", "radiologist")
    assert client.get("/api/auth/me", headers=h).json()["role"] == "radiologist"
    assert client.post("/api/auth/login", json={"email": "doc@t.io", "password": "Wrong123!"}).status_code == 401
    assert client.get("/api/patients").status_code == 401
    client.post("/api/auth/logout", headers=h)
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_lockout_after_failed_logins(client):
    register(client, "lock@t.io", "researcher")
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "lock@t.io", "password": "Wrong123!"})
    assert client.post("/api/auth/login", json={"email": "lock@t.io", "password": "Passw0rd!"}).status_code == 423


def test_roles(client):
    ds = register(client, "ds@t.io", "data_scientist")
    assert client.post("/api/patients", json={"patient_code": "X"}, headers=ds).status_code == 403
    assert client.get("/api/users", headers=ds).status_code == 403


def test_patient_case_and_upload(client):
    h = register(client, "rad@t.io", "radiologist")
    p = client.post("/api/patients", json={"patient_code": "ANON-1", "age": 61, "gender": "Male",
                                           "risk_factors": ["Diabetes"]}, headers=h)
    assert p.status_code == 201
    c = client.post("/api/cases", json={"patient_id": p.json()["id"]}, headers=h).json()
    assert c["case_code"].startswith("CASE-")
    url = f"/api/cases/{c['id']}/images"
    assert client.post(url, files={"file": ("x.png", b"not an image", "image/png")}, headers=h).status_code == 422
    ok = client.post(url, files={"file": ("a.png", png(), "image/png")}, headers=h)
    assert ok.status_code == 201
    assert client.get(f"/api/cases/{c['id']}", headers=h).json()["status"] == "uploaded"


def test_preprocessing_chain():
    img = cv2.imdecode(np.frombuffer(png(), np.uint8), cv2.IMREAD_GRAYSCALE)
    pre = preprocess(LoadedImage(img, None, "PNG", img.shape))
    assert pre.original.shape == (512, 512) and pre.preprocessed.shape == (512, 512)
    assert pre.model_input.dtype == np.float32 and 0 <= pre.model_input.min() <= pre.model_input.max() <= 1
    x0, y0, x1, y1 = pre.roi_bbox
    assert 0 <= x0 < x1 <= 512 and 0 <= y0 < y1 <= 512
