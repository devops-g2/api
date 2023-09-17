from .common import client, session


def test_root_working():
    r = client.get('/')
    assert r.status_code == 200
