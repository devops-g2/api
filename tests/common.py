import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from api import main
from api.models import Endpointer


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    # f = open('tmp.db', 'w')
    # f.close()
    TEST_DB = tempfile.NamedTemporaryFile(mode="w+")
    engine = create_engine(f"sqlite:///{Path(TEST_DB.name)}")
    Endpointer.init(engine)
    with Session(Endpointer.engine) as session:
        yield session


def mkclient() -> TestClient:
    return TestClient(main.app)


@pytest.fixture()
def created_objs(session: Session, path, objs):
    for obj in objs:
        mkclient().post(path, json=obj)


@pytest.fixture()
def has_added_readonly_stuff():
    def has_added_readonly_stuff(data, obj, id=1, **kwargs):
        if id:
            return data == obj | {"id": id}
        else:
            return data == obj | kwargs

    return has_added_readonly_stuff


def test_create(session: Session, path, obj_1, has_added_readonly_stuff):
    r = mkclient().post(path, json=obj_1)
    assert r.status_code == 200
    assert has_added_readonly_stuff(r.json(), obj_1)


@pytest.fixture()
def objs(obj_1, obj_2):
    return obj_1, obj_2


def test_create_and_read_one(created_objs, path, obj_1, has_added_readonly_stuff):
    obj_n = 1
    r = mkclient().get(f"{path}/{obj_n}")
    assert r.status_code == 200
    assert has_added_readonly_stuff(r.json(), obj_1)


def test_create_and_read_many(created_objs, path, objs):
    r = mkclient().get(path)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == len(objs)
    if "id" in data[1]:
        assert data[1]["id"] == 2


def test_create_and_update(
    created_objs,
    obj_1,
    patched_obj_1,
    path,
    has_added_readonly_stuff,
):
    obj_n = 1
    patched_obj_1 = obj_1 | patched_obj_1
    patch_r = mkclient().patch(f"{path}/{obj_n}", json=patched_obj_1)
    assert patch_r.status_code == 200
    assert has_added_readonly_stuff(patch_r.json(), patched_obj_1)
    get_r = mkclient().get(f"{path}/{obj_n}")
    assert has_added_readonly_stuff(get_r.json(), patched_obj_1)


def test_create_and_delete(created_objs, path):
    obj_n = 1
    delete_r = mkclient().delete(f"{path}/{obj_n}")
    assert delete_r.status_code == 200
    assert delete_r.json() == {"ok": True}
    get_r = mkclient().delete(f"{path}/{obj_n}")
    assert get_r.status_code == 404
    assert len(mkclient().get(path).json()) == 1


def test_skip(created_objs, path):
    client = mkclient()
    skip_0 = client.get(path + '?skip=0')
    skip_1 = client.get(path + '?skip=1')
    skip_2 = client.get(path + '?skip=2')
    assert len(skip_0.json()) == 2
    assert len(skip_1.json()) == 1
    assert len(skip_2.json()) == 0


def test_limit(created_objs, path):
    client = mkclient()
    limit_0 = client.get(path + '?limit=0')
    limit_1 = client.get(path + '?limit=1')
    limit_2 = client.get(path + '?limit=2')
    assert len(limit_0.json()) == 0
    assert len(limit_1.json()) == 1
    assert len(limit_2.json()) == 2


def test_skip_and_limit(created_objs, path, obj_1, obj_2):
    client = mkclient()
    no_skip_limit_1 = client.get(path + '?skip=0&limit=1')
    assert len(no_skip_limit_1.json()) == 1
    if 'id' in (got := no_skip_limit_1.json()[0]):
        assert got['id'] == 1
    else:
        assert got == obj_1
    no_limit_skip_1 = client.get(path + '?limit=2&skip=1')
    assert len(no_limit_skip_1.json()) == 1
    if 'id' in (got := no_limit_skip_1.json()[0]):
        assert got['id'] == 2
    else:
        assert got == obj_2

    
    
