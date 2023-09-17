from .common import mkclient


def test_root_working() -> None:
    r = mkclient().get("/")
    assert r.status_code == 200
