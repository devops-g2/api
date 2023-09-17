from fastapi.testclient import TestClient
from api.models import Endpointer
from sqlmodel import create_engine, Session
# from api import User, Post, TaggedPost, app
from pathlib import Path
from api import main
import tempfile
import pytest
from sqlmodel import SQLModel
from dataclasses import dataclass


@pytest.fixture()
def session():
    TEST_DB = tempfile.NamedTemporaryFile(mode='w')
    engine = create_engine(f'sqlite:///{Path(TEST_DB.name)}')
    Endpointer.init(engine)
    with Session(Endpointer.engine) as session:
        yield session


def add(session, obj, clazz):
    db_obj = clazz.Table.from_orm(obj)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)


def mkclient():
    return TestClient(main.app)
