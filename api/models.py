from sqlmodel import SQLModel, Field, Relationship, func, create_engine, Session
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


class Named(SQLModel):
    name: str


class Authored(SQLModel):
    author: int = Field(foreign_key="user.id")


class Index(SQLModel):
    id: int


class Table(SQLModel):
    id: int | None = Field(primary_key=True, index=True, default=None)


class DatedTable(Table):
    created_at: datetime = Field(default_factory=func.now)
    updated_at: datetime = Field(
        default_factory=func.now, sa_column_kwargs={"onupdate": func.now()}
    )


# Implementations


class UserBase(Named):
    email: str
    password: str


class UserCreate(UserBase):
    email: str
    password: str
    pass


class User(UserBase, DatedTable, table=True):
    pass


class CategoryBase(Named):
    pass
    # threads: List['Thread'] = Relationship(back_populates='category')


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase, Table, table=True):
    pass
    # threads: list['Thread'] = Relationship(back_populates='category_id')


class ThreadBase(Named, Authored):
    category_id: int = Field(foreign_key="category.id")


class ThreadCreate(ThreadBase):
    pass


class Thread(ThreadBase, DatedTable, table=True):
    pass
    # category: Category = Relationship(back_populates='threads')
    # posts: list['Post'] = Relationship(back_populates='thread')


class PostBase(Authored):
    thread_id: int = Field(foreign_key="thread.id")
    content: str


class PostCreate(PostBase):
    pass


class Post(PostBase, DatedTable, table=True):
    pass
    # thread: Thread = Relationship(back_populates='thread')


ModelInfo = namedtuple("ModelInfo", ("table", "creator", "prefix"))


MODELS: dict[str, ModelInfo] = {
    "user": ModelInfo(User, UserCreate, "users"),
    "category": ModelInfo(Category, CategoryCreate, "categories"),
    "thread": ModelInfo(Thread, ThreadCreate, "threads"),
    "post": ModelInfo(Post, PostCreate, "posts"),
}


DB = Path("forum.db")
engine = create_engine(
    f"sqlite:///{DB}", echo=True, connect_args={"check_same_thread": False}
)

SessionLocal = Session(engine)


def get_db():
    session = Session(engine)
    try:
        yield session
        session.commit()
    finally:
        session.close()


def _seed_table(model: ModelInfo, objs):
    with Session(engine) as session:
        for obj in objs:
            create_obj = model.creator(**obj)
            db_obj = model.table.from_orm(create_obj)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)


def seed():
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


def create_all(*, wipe_old: bool = False, do_seed: bool = False):
    if wipe_old:
        DB.unlink()
    SQLModel.metadata.create_all(bind=engine)
    if do_seed:
        seed()
