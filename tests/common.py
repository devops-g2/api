import tempfile
from pathlib import Path
from typing import Generator, TypeVar

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from api import main
from api.models import Endpointer


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    TEST_DB = tempfile.NamedTemporaryFile(mode="w")
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
            return data == obj | {'id': id}
        else:
            return data == obj | kwargs
    return has_added_readonly_stuff


def test_create(session: Session, path, obj_1, has_added_readonly_stuff):
    r = mkclient().post(
        path,
        json=obj_1
    )
    assert r.status_code == 200
    assert has_added_readonly_stuff(r.json(), obj_1)

@pytest.fixture()
def objs(obj_1, obj_2):
    return obj_1, obj_2


def test_create_and_read_one(created_objs, path, obj_1, has_added_readonly_stuff):
    obj_n = 1
    r = mkclient().get(f'{path}/{obj_n}')
    assert r.status_code == 200
    assert has_added_readonly_stuff(r.json(), obj_1)

def test_create_and_read_many(created_objs, path, objs):
    r = mkclient().get(path)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == len(objs)
    if 'id' in data[1]:
        assert data[1]['id'] == 2


def test_create_and_update(created_objs, obj_1, patched_obj_1, path, has_added_readonly_stuff):
    obj_n = 1
    patched_obj_1 = obj_1 | patched_obj_1
    patch_r = mkclient().patch(f'{path}/{obj_n}', json=patched_obj_1)
    assert patch_r.status_code == 200
    assert has_added_readonly_stuff(patch_r.json(), patched_obj_1)
    get_r = mkclient().get(f'{path}/{obj_n}')
    assert has_added_readonly_stuff(get_r.json(), patched_obj_1)


def test_create_and_delete(created_objs, path):
    obj_n = 1
    delete_r = mkclient().delete(f'{path}/{obj_n}')
    assert delete_r.status_code == 200
    assert delete_r.json() == {'ok': True}
    get_r = mkclient().delete(f'{path}/{obj_n}')
    assert get_r.status_code == 404
    assert len(mkclient().get(path).json()) == 1

