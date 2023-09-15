from __future__ import annotations
from functools import partial

from typing import Annotated, Type
from datetime import datetime  # noqa: TCH003
from pathlib import Path
from fastapi import HTTPException, Depends, APIRouter
from typing import Generator

from sqlmodel import Field, Session, SQLModel, create_engine, func, select, Relationship
from pydantic import BaseModel, root_validator
from .utils import query_factory, sort_factory, FILTER, SORT



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


def pagination(skip: int = 0, limit: int | None = None) -> dict[str, int | None]:
    return {"skip": skip, "limit": limit}


Pagination = Annotated[dict[str, int | None], Depends(pagination)]


class ElemNotFoundException(HTTPException):
    def __init__(self: ElemNotFoundException, elem: str, n: int) -> None:
        self.elem = elem
        self.n = n

    def __str__(self: ElemNotFoundException) -> str:
        return f"{self.elem} #{self.n} not found"


ID_FIELD = Field(primary_key=True, index=True, default=None)  # noqa: A003

USER_ID_FIELD = Field(foreign_key='user.id')
TAG_ID_FIELD = Field(foreign_key='tag.id', primary_key=True)
POST_ID_FIELD = Field(foreign_key='post.id', primary_key=True)

CREATED_AT_FIELD = Field(default_factory=func.now)

UPDATED_AT_FIELD = Field(
    default_factory=func.now,
    sa_column_kwargs={"onupdate": func.now()},
)


class Index(SQLModel):
    id: int  # noqa: A003


class ConfirmationModel(SQLModel):
    ok: bool


class Endpointed:
    ROUTER = APIRouter()


    # class Table:
    #     pass


    # class Creator:
    #     pass


    # class Updater:
    #     pass

    # class Reader:
    #     pass


    # @classmethod
    # def __init_subclass__(cls):
        # cls.Table = cls.Table
        # cls.Reader = getattr(cls, 'Reader', cls.Table)

    @classmethod
    def obj_apply(cls, obj, session):
        return obj

    @classmethod
    def get_tags(cls):
        return [cls.PREFIX.replace('_', ' ')]

    @classmethod
    def get_filter_query(cls):
        # print(dir(cls.Table))
        return cls.Table.__fields__

    @classmethod
    def get_pk(cls):
        return cls.Table.__table__.primary_key.columns.keys()[0]

    @classmethod
    def select(cls):
        return select(cls.Table)

    @classmethod
    def query_apply(cls, query, *args, **kwargs):
        return query

    @classmethod
    def paginate(cls, query, pagination):
        return query \
            .offset(pagination['skip']) \
            .limit(pagination['limit'])

    @classmethod
    def sort(cls, query, sort_):
        if sort_:
            field = getattr(cls.Table, sort_.get("sort", cls.get_pk()))
            order = field.desc() if sort_.get("reverse", False) else field
            query = query.order_by(order)
            return query
        return query
       
    @classmethod
    def build_query(cls, sort_, pagination, *args, **kwargs):
        query = cls.select()
        query = cls.query_apply(query, *args, **kwargs)
        query = cls.sort(query, sort_)
        query = cls.paginate(query, pagination)
        return query



    @classmethod
    def create(cls):
        def route(
            *,
            session: Session = Depends(get_db),
            obj  # type: cls.Creator (really annotated at route initializationy)
        ):
            db_obj = cls.Table.from_orm(obj)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        return route

    @classmethod
    def get_all(cls):
        def route(
            *,
            session: Session = Depends(get_db),
            pagination: Pagination,
            sort_: SORT = sort_factory(cls.Table)
        ):
            query = cls.build_query(sort_, pagination)
            objs = session.exec(query).all()
            return [cls.obj_apply(obj, session) for obj in objs]
        return route

    @classmethod
    def get_one(cls):
        def route(
            *,
            session: Session = Depends(get_db),
            obj_id: int,
        ):
            if not (obj := session.get(cls.Table, obj_id)):
               raise ElemNotFoundException(cls.__name__, obj_id)
            return cls.obj_apply(obj, session)
        return route

    @classmethod
    def update(cls):
        def route(
            *,
            session: Session = Depends(get_db),
            obj_id: int,
            obj  # type: cls.Updater (really annotated at route initialization)
        ):
            if not (db_obj := session.get(cls.Table, obj_id)):
                raise ElemNotFoundException(cls.__name__, obj_id)
            
            obj_data = obj.dict(exclude_unset=True)
            for key, value in obj_data.items():
                setattr(db_obj, key, value)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        return route

    @classmethod
    def delete(cls):
        def route(
            *,
            session: Session = Depends(get_db),
            obj_id: int
        ):
            if not (obj := session.get(cls.Table, obj_id)):
                raise ElemNotFoundException(cls.__name__, obj_id)
            session.delete(obj)
            session.commit()
            return {'ok': True}
        return route

    @classmethod
    def include_endpoints(cls, app):
        tags = cls.get_tags()

        # This rinky dink hack is because we can't typehint obj with
        # obj: cls.<Model class>
        # since pydantic is not aware of cls at compile time.
        create = cls.create()
        create.__annotations__['obj'] = cls.Creator
        # get_all.__annotations__['obj'] = cls.Table
        update = cls.update()
        update.__annotations__['obj'] = cls.Updater

        # create
        cls.ROUTER.add_api_route(
            methods=['POST'],
            path=f'/{cls.PREFIX}/',
            endpoint=create,
            tags=tags,
            name=f'Create a {cls.__name__.lower()}'
        )

        # many
        cls.ROUTER.add_api_route(
            methods=['GET'],
            path=f'/{cls.PREFIX}/',
            endpoint=cls.get_all(),
            response_model=list[getattr(cls, 'Reader', cls.Table)],
            tags=tags,
            name=f'Get all {tags[0]}'
        )

        # one
        cls.ROUTER.add_api_route(
            methods=['GET'],
            path=f'/{cls.PREFIX}/{{obj_id}}',
            endpoint=cls.get_one(),
            response_model=getattr(cls, 'Reader', cls.Table),
            tags=tags,
            name=f'Get one {cls.__name__.lower()}'
        )

        # update
        cls.ROUTER.add_api_route(
            methods=['PATCH'],
            path=f'/{cls.PREFIX}/{{obj_id}}',
            endpoint=update,
            response_model=getattr(cls, 'Reader', cls.Table),
            tags=tags,
            name=f'Update a {cls.__name__.lower()}'
        )

        # delete
        cls.ROUTER.add_api_route(
            methods=['DELETE'],
            path=f'/{cls.PREFIX}/{{obj_id}}',
            endpoint=cls.delete(),
            response_model=ConfirmationModel,
            tags=tags,
            name=f'Delete a {cls.__name__.lower()}'
        )

    @staticmethod
    def include_all_subclass_endpoints(app):
        for subclass in Endpointed.__subclasses__():
            subclass.include_endpoints(app)

    @classmethod
    def seed(cls):
        with Session(engine) as session:
            for obj in cls.SEED_OBJS:
                create_obj = cls.Creator(**obj)
                db_obj = cls.Table.from_orm(create_obj)
                session.add(db_obj)
                session.commit()
                session.refresh(db_obj)

    @staticmethod
    def seed_all_subclasses():
        for subclass in Endpointed.__subclasses__():
            subclass.seed()


class User(Endpointed):
    PREFIX = 'users'

    SEED_OBJS = (
        {'name': 'User1', 'email': 'foo@bar.com', 'password': '12345'},
    )
    
    class Table(SQLModel, table=True):
        __tablename__ = 'user'

        id: int | None = ID_FIELD
        name: str | None
        email: str | None
        password: str | None

    class Creator(SQLModel):
        name: str
        email: str
        password: str

    class Updater(SQLModel):
        name: str | None = None
        email: str | None = None
        password: str | None = None


class TaggedPost(Endpointed):
    PREFIX = 'tagged_posts'

    SEED_OBJS = (
        {'tag_id': 1, 'post_id': 1},
    )
    
    class Table(SQLModel, table=True):
        __tablename__ = 'tagged_post'
        
        # id: int = ID_FIELD
        tag_id: int | None = TAG_ID_FIELD
        post_id: int | None = POST_ID_FIELD

    class Creator(SQLModel):
        tag_id: int
        post_id: int

    class Updater(SQLModel):
        tag_id: int | None = None
        post_id: int | None = None


class Tag(Endpointed):
    PREFIX = 'tags'

    SEED_OBJS = (
        {'name': 'Tag1'},
    )
    
    class Table(SQLModel, table=True):
        __tablename__ = 'tag'

        id: int | None = ID_FIELD
        name: str | None

        # posts: list['Post.Table'] = Relationship(back_populates='tags', link_model=TaggedPost.Table)

    class Creator(SQLModel):
        name: str

    class Updater(SQLModel):
        name: str | None = None


class Post(Endpointed):
    PREFIX = 'posts'

    SEED_OBJS = (
        # {'name': 'Post1', 'content': 'Post1 content', 'author': 1, 'tags': [Tag.Creator(**Tag.SEED_OBJS[0])]},
        {'name': 'Post1', 'content': 'Post1 content', 'author': 1},
    )

    class Base(SQLModel):
        id: int | None = ID_FIELD
        name: str | None
        content: str | None
        author: int | None = USER_ID_FIELD
        created_at: datetime | None = CREATED_AT_FIELD
        updated_at: datetime | None = UPDATED_AT_FIELD
    
    class Table(Base, table=True):
        __tablename__ = 'post'

    class Creator(SQLModel):
        name: str
        content: str
        author: int

    class Updater(SQLModel):
        name: str | None = None
        content: str | None = None
        author: int | None = None

    class Reader(Base):
        tags: list[Tag.Table] | None

    class Filter(Base):
        tags: list[int]

    @classmethod
    def obj_apply(cls, obj, session):
        tagged_posts = session.exec(
            select(TaggedPost.Table)
            .where(TaggedPost.Table.post_id == obj.id)
        ).all()
        tags = [
            session.get(Tag.Table, tagged_post.tag_id)
            for tagged_post in tagged_posts
        ]
        new_obj = obj.copy(update={'tags': tags})
        return new_obj



    @classmethod
    def get_all(cls):
        def route(
            *,
            session: Session = Depends(get_db),
            pagination: Pagination,
            sort_: SORT = sort_factory(cls.Table),
            filter: Annotated[cls.Filter]
        ):
            query = cls.build_query(sort_, pagination)
            objs = session.exec(query).all()
            return [cls.obj_apply(obj, session) for obj in objs]
        route.__annotations__['filter'] = cls.Filter


class Comment(Endpointed):
    PREFIX = 'comments'

    SEED_OBJS = ()

    class Table(SQLModel, table=True):
        __tablename__ = 'comment'
        
        id: int | None = ID_FIELD
        name: str | None
        content: str | None
        author: int | None = USER_ID_FIELD
        created_at: datetime | None = CREATED_AT_FIELD
        updated_at: datetime | None = UPDATED_AT_FIELD

    class Creator(SQLModel):
        name: str
        content: str
        author: int

    class Updater(SQLModel):
        name: str | None = None
        content: str | None = None
        author: int | None = None




# def _seed_table(model: ModelInfo, objs: Iterable[dict[str, Any]]) -> None:


# def seed() -> None:
#     _seed_table(
#         MODELS["user"],
#         (
#             {"name": "User 1", "email": "user1@example.com", "password": "user1"},
#             {"name": "User 2", "email": "user2@example.com", "password": "user2"},
#             {"name": "User 3", "email": "user3@example.com", "password": "user3"},
#         ),
#     )
#     _seed_table(
#         MODELS["category"],
#         (
#             {"name": "Category 1"},
#             {"name": "Category 2"},
#             {"name": "Category 3"},
#         ),
#     )
#     _seed_table(
#         MODELS["thread"],
#         (
#             {"name": "Thread 1", "category_id": 1, "author": 1},
#             {"name": "Thread 2", "category_id": 1, "author": 2},
#             {"name": "Thread 3", "category_id": 2, "author": 3},
#         ),
#     )
#     _seed_table(
#         MODELS["post"],
#         (
#             {"thread_id": 1, "author": 1, "content": "Post 1 content"},
#             {"thread_id": 1, "author": 2, "content": "Post 2 content"},
#             {"thread_id": 2, "author": 3, "content": "Post 3 content"},
#             {"thread_id": 2, "author": 1, "content": "Post 4 content"},
#             {"thread_id": 3, "author": 2, "content": "Post 5 content"},
#             {"thread_id": 3, "author": 3, "content": "Post 6 content"},
#         ),
#     )

# print(CommentModel.get_all())


def create_all(*, wipe_old: bool = False, do_seed: bool = False) -> None:
    if wipe_old:
        DB.unlink(missing_ok=True)
    SQLModel.metadata.create_all(bind=engine)
    if do_seed:
        Endpointed.seed_all_subclasses()
        # seed()

print(User.get_filter_query())
# print(User.Table.__fields__)
# print(dir(Post.Creator))
# print(Post.Creator.schema())
# print(Post.Reader.__signature__)
print(dir(Post.Reader))
# Post.Reader.__name__ = 'Post.Reader'
# print(Post.Reader.__dict__)
# print(Post.Reader.__fields__)
# # print(Post.Reader.dict(exclude_unset=True))
# print(Post.Reader.)
# for k in dir(Post.Reader):
#     try:
#         print(k, getattr(Post.Reader, k))
#     except AttributeError:
#         print(f'error: {k}')

# print(str(Post.Reader.__repr__))
