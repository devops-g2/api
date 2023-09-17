import tempfile
from pathlib import Path

from typing import Generator, Type, TypeVar
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel

from api import main
from api.models import Endpointer


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    TEST_DB = tempfile.NamedTemporaryFile(mode="w")
    engine = create_engine(f"sqlite:///{Path(TEST_DB.name)}")
    Endpointer.init(engine)
    with Session(Endpointer.engine) as session:
        yield session


T = TypeVar('T', bound=type[Endpointer])


def add(session: Session, obj: SQLModel, clazz: T) -> None:
    db_obj = clazz.Table.from_orm(obj)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)


def mkclient() -> TestClient:
    return TestClient(main.app)
