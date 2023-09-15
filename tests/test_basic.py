from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import app


client = TestClient(app)

def test_root_working():
    r = client.get('/')
    assert r.status_code == 200
