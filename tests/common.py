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


# T = TypeVar("T", bound=type[Endpointer])


# def add(session: Session, obj: SQLModel, clazz: T) -> None:
#     db_obj = clazz.Table.model_validate(obj)
#     session.add(db_obj)
#     session.commit()
#     session.refresh(db_obj)


def mkclient() -> TestClient:
    return TestClient(main.app)


@pytest.fixture()
def created_objs(session: Session, path, objs):
    for obj in objs:
        mkclient().post(path, json=obj)


def test_create(session: Session, path, obj_1):
    r = mkclient().post(
        path,
        json=obj_1
    )
    assert r.status_code == 200
    assert r.json() == obj_1 | {'id': 1}

def test_create_and_read_one(created_objs, path, obj_1):
    obj_n = 1
    r = mkclient().get(f'{path}/{obj_n}')
    assert r.status_code == 200
    data = r.json()
    assert data == obj_1 | {'id': 1}

def test_create_and_read_many(created_objs, path, objs):
    r = mkclient().get(path)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == len(objs)
    assert data[1]['id'] == 2


def test_create_and_update(created_objs, obj_1, path):
    obj_n = 1
    patched_obj_1 = obj_1 | {'name': 'Not Alice'}
    patch_r = mkclient().patch(f'{path}/{obj_n}', json=patched_obj_1)
    assert patch_r.status_code == 200
    patch_data = patch_r.json()
    assert patch_data == patched_obj_1 | {'id': obj_n}
    get_r = mkclient().get(f'{path}/{obj_n}')
    get_data = get_r.json()
    assert get_data == patched_obj_1 | {'id': obj_n}


def test_create_and_delete(created_objs, path):
    obj_n = 1
    delete_r = mkclient().delete(f'{path}/{obj_n}')
    assert delete_r.status_code == 200
    assert delete_r.json() == {'ok': True}
    get_r = mkclient().delete(f'{path}/{obj_n}')
    assert get_r.status_code == 404
    assert len(mkclient().get(path).json()) == 1

