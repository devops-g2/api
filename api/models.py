from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime  # noqa: TCH003
from pathlib import Path
from typing import Any, Generator, Iterable

from sqlmodel import Field, Session, SQLModel, create_engine, func


ID_FIELD = Field(primary_key=True, index=True, default=None)  # noqa: A003

USER_ID_FIELD = Field(foreign_key='user.id')
TAG_ID_FIELD = Field(foreign_key='tag.id')
POST_ID_FIELD = Field(foreign_key='post.id')

CREATED_AT_FIELD = Field(default_factory=func.now)

UPDATED_AT_FIELD = Field(
    default_factory=func.now,
    sa_column_kwargs={"onupdate": func.now()},
)


class Index(SQLModel):
    id: int  # noqa: A003


class Endpointed:
    @classmethod
    def get_all(cls):
        print(cls.Creator)


class User:
    class Table(SQLModel, table=True):
        __tablename__ = 'User'

        id: int = ID_FIELD
        name: str
        email: str
        password: str

    class Creator:
        name: str
        email: str
        password: str

    class Updater:
        name: str | None = None
        email: str | None = None
        password: str | None = None


class Tag:
    class Table(SQLModel, table=True):
        __tablename__ = 'tag'

        id: int = ID_FIELD
        name: str

    class Creator:
        name: str

    class Updater:
        name: str | None = None


class Post:
    class Table(SQLModel, table=True):
        __tablename__ = 'post'

        id: int = ID_FIELD
        name: str
        content: str
        author: int = USER_ID_FIELD
        created_at: datetime = CREATED_AT_FIELD
        updated_at: datetime = UPDATED_AT_FIELD

    class Creator:
        name: str
        content: str
        author: int

    class Updater:
        name: str | None = None
        content: str | None = None
        author: int | None = None


class TaggedPost:
    class Table(SQLModel, table=True):
        __tablename__ = 'tagged_post'
        
        id: int = ID_FIELD
        tag_id: int = TAG_ID_FIELD
        post_id: int = POST_ID_FIELD

    class Creator:
        tag_id: int
        post_id: int

    class Updater:
        tag_id: int | None = None
        post_id: int | None = None


class CommentModel(Endpointed):
    class Table(SQLModel, table=True):
        __tablename__ = 'comment'
        
        id: int = ID_FIELD
        name: str
        content: str
        author: int = USER_ID_FIELD
        created_at: datetime = CREATED_AT_FIELD
        updated_at: datetime = UPDATED_AT_FIELD

    class Creator:
        name: str
        content: str
        author: int

    class Updater:
        name: str | None = None
        content: str | None = None
        author: int | None = None


DB = Path("forum.db")
engine = create_engine(
    f"sqlite:///{DB}",
    echo=True,
    connect_args={"check_same_thread": False},
)

SessionLocal = Session(engine)


def get_db() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    finally:
        session.close()


def _seed_table(model: ModelInfo, objs: Iterable[dict[str, Any]]) -> None:
    with Session(engine) as session:
        for obj in objs:
            create_obj = model.creator(**obj)
            db_obj = model.table.from_orm(create_obj)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)


def seed() -> None:
    _seed_table(
        MODELS["user"],
        (
            {"name": "User 1", "email": "user1@example.com", "password": "user1"},
            {"name": "User 2", "email": "user2@example.com", "password": "user2"},
            {"name": "User 3", "email": "user3@example.com", "password": "user3"},
        ),
    )
    _seed_table(
        MODELS["category"],
        (
            {"name": "Category 1"},
            {"name": "Category 2"},
            {"name": "Category 3"},
        ),
    )
    _seed_table(
        MODELS["thread"],
        (
            {"name": "Thread 1", "category_id": 1, "author": 1},
            {"name": "Thread 2", "category_id": 1, "author": 2},
            {"name": "Thread 3", "category_id": 2, "author": 3},
        ),
    )
    _seed_table(
        MODELS["post"],
        (
            {"thread_id": 1, "author": 1, "content": "Post 1 content"},
            {"thread_id": 1, "author": 2, "content": "Post 2 content"},
            {"thread_id": 2, "author": 3, "content": "Post 3 content"},
            {"thread_id": 2, "author": 1, "content": "Post 4 content"},
            {"thread_id": 3, "author": 2, "content": "Post 5 content"},
            {"thread_id": 3, "author": 3, "content": "Post 6 content"},
        ),
    )

print(CommentModel.get_all())


def create_all(*, wipe_old: bool = False, do_seed: bool = False) -> None:
    if wipe_old:
        DB.unlink(missing_ok=True)
    SQLModel.metadata.create_all(bind=engine)
    if do_seed:
        seed()
