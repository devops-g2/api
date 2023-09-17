from .common import mkclient, session


def test_root_working():
    r = mkclient().get('/')
    assert r.status_code == 200
