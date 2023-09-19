from __future__ import annotations

import inspect
import warnings
from datetime import datetime  # noqa: TCH003
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ClassVar,
    Generator,
    Protocol,
    TypeVar,
)

import sqlalchemy
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy.exc import SAWarning
from sqlmodel import (
    Field,
    Session,
    SQLModel,
    func,
    select,
)

# SQLModelMetaclass
from .utils import SORT, sort_factory

if TYPE_CHECKING:
    from enum import Enum

    from mypy_extensions import DefaultNamedArg, NamedArg
    from sqlalchemy.future import Engine as SQLAlchemyEngine
    from sqlmodel.sql.expression import SelectOfScalar

warnings.filterwarnings("ignore", category=SAWarning)


def pagination(skip: int = 0, limit: int | None = None) -> dict[str, int | None]:
    return {"skip": skip, "limit": limit}


Pagination = Annotated[dict[str, int | None], Depends(pagination)]


class ElemNotFoundException(HTTPException):
    status_code = 404
    def __init__(self: ElemNotFoundException, elem: str, n: int) -> None:
        self.elem = elem
        self.n = n

    def __str__(self: ElemNotFoundException) -> str:
        return f"{self.elem} #{self.n} not found"

    @property
    def detail(self):
        return str(self)


ID_FIELD = Field(primary_key=True, index=True, default=None)

USER_ID_FIELD = Field(foreign_key="user.id")
TAG_ID_PRIMARY_FIELD = Field(foreign_key="tag.id", primary_key=True)
POST_ID_PRIMARY_FIELD = Field(foreign_key="post.id", primary_key=True)
POST_ID_FIELD = Field(foreign_key='post.id')

CREATED_AT_FIELD = Field(default=None, sa_column_kwargs={"default": func.now()})
UPDATED_AT_FIELD = Field(
    default=None,
    sa_column_kwargs={"default": func.now(), "onupdate": func.now()},
)


class ConfirmationModel(SQLModel):
    ok: bool


M = TypeVar("M", bound=SQLModel, covariant=True)
T = TypeVar("T")


class Endpointer(Protocol):
    ROUTER: ClassVar[APIRouter] = APIRouter()
    prefix: ClassVar[str]
    SEED_OBJS: ClassVar[tuple[dict[str, Any]] | tuple[()]]

    engine: ClassVar[SQLAlchemyEngine]

    class Table(SQLModel):
        pass

    class Creator(SQLModel):
        pass

    class Updater(SQLModel):
        pass

    @classmethod
    def endpointed_init(cls: type[Endpointer], app: FastAPI) -> None:
        raise NotImplementedError

    @classmethod
    def init_app(cls: type[Endpointer], app: FastAPI) -> None:
        cf = inspect.currentframe()
        if not cf:
            raise RuntimeError
        f_name_of_myself = cf.f_code.co_name
        my_f = getattr(cls, f_name_of_myself)
        my_f_path = my_f.__qualname__
        f_origin_class_name = my_f_path.split(".")[0]
        if cls.__name__ == f_origin_class_name:  # is original superclass
            for subclass in cls.__subclasses__():
                subclass.include_endpoints(app)
            app.include_router(cls.ROUTER)
        else:                                    # is inheriting subclass
            cls.endpointed_init(app)

    @classmethod
    def init(
        cls: type[Endpointer],
        engine: SQLAlchemyEngine,
        *,
        do_seed: bool = False,
    ) -> None:
        cls.engine = engine
        SQLModel.metadata.create_all(bind=cls.engine)
        if do_seed:
            for subclass in Endpointer.__subclasses__():
                subclass.seed()

    @classmethod
    def get_db(cls: type[Endpointer]) -> Generator[Session, None, None]:
        session = Session(cls.engine)
        try:
            yield session
            session.commit()
        finally:
            session.close()

    @classmethod
    def obj_apply(cls, obj: Table, session: Session) -> Table:
        return obj

    @classmethod
    def get_tags(cls: type[Endpointer]) -> list[str | Enum]:
        return [cls.prefix.replace("_", " ")]

    @classmethod
    def get_pk(cls: type[Endpointer]) -> Any:
        return cls.Table.__table__.primary_key.columns.keys()[0]  # type: ignore


    @classmethod
    def select(cls: type[Endpointer]) -> SelectOfScalar[Table]:
        return select(cls.Table)


    @classmethod
    def query_apply(
        cls, query: SelectOfScalar[Table], *args: Any, **kwargs: Any,
    ) -> SelectOfScalar[Table]:
        return query

    @classmethod
    def paginate(
        cls, query: SelectOfScalar[Table], pagination: Pagination,
    ) -> SelectOfScalar[Table]:
        return query.offset(pagination["skip"]).limit(pagination["limit"])

    @classmethod
    def sort(cls, query: SelectOfScalar[Table], sort_: SORT) -> SelectOfScalar[Table]:
        if sort_:
            field = getattr(cls.Table, sort_.get("sort", cls.get_pk()))
            order = field.desc() if sort_.get("reverse", False) else field
            return query.order_by(order)
        return query

    @classmethod
    def create(
        cls,
    ) -> Callable[[DefaultNamedArg(Session, "session"), NamedArg(Any, "obj")], Table]:
        def route(
            *, session: Session = Depends(cls.get_db), obj: Endpointer.Creator,
        ) -> Endpointer.Table:
            db_obj = cls.Table.from_orm(obj)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj

        route.__annotations__["obj"] = cls.Creator
        return route

    @classmethod
    def _do_get_all(
        cls,
        session: Session,
        pagination: Pagination,
        sort_: SORT,
        *args: Any,
        **kwargs: Any,
    ):
        query = cls.select()
        query = cls.query_apply(query, session=session, *args, **kwargs)
        query = cls.sort(query, sort_)
        query = cls.paginate(query, pagination)
        objs = session.exec(query).all()
        return [cls.obj_apply(obj, session) for obj in objs]

    @classmethod
    def get_all(
        cls,
    ):
        def route(
            *,
            session: Session = Depends(cls.get_db),
            pagination: Pagination,
            sort_: SORT = sort_factory(cls.Table),
        ):
            return cls._do_get_all(session=session, pagination=pagination, sort_=sort_)

        return route

    @classmethod
    def get_one(
        cls,
    ) -> Callable[
        [DefaultNamedArg(Session, "session"), NamedArg(int, "obj_id")], Table,
    ]:
        def route(
            *,
            session: Session = Depends(cls.get_db),
            obj_id: int,
        ) -> Endpointer.Table:
            if not (obj := session.get(cls.Table, obj_id)):
                raise ElemNotFoundException(cls.__name__, obj_id)
            return cls.obj_apply(obj, session)

        return route

    @classmethod
    def update(
        cls,
    ) -> Callable[
        [
            DefaultNamedArg(Session, "session"),
            NamedArg(int, "obj_id"),
            NamedArg(Table, "obj"),
        ],
        Table,
    ]:
        def route(
            *,
            session: Session = Depends(cls.get_db),
            obj_id: int,
            obj: Endpointer.Table,
        ) -> Endpointer.Table:
            if not (db_obj := session.get(cls.Table, obj_id)):
                raise ElemNotFoundException(cls.__name__, obj_id)

            obj_data = obj.model_dump(exclude_unset=True)
            for key, value in obj_data.items():
                setattr(db_obj, key, value)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj

        route.__annotations__["obj"] = cls.Updater
        return route

    @classmethod
    def delete(
        cls,
    ) -> Callable[
        [DefaultNamedArg(Session, "session"), NamedArg(int, "obj_id")], dict[str, bool],
    ]:
        def route(
            *, session: Session = Depends(cls.get_db), obj_id: int,
        ) -> dict[str, bool]:
            if not (obj := session.get(cls.Table, obj_id)):
                raise ElemNotFoundException(cls.__name__, obj_id)
            session.delete(obj)
            session.commit()
            return {"ok": True}

        return route

    @classmethod
    def include_endpoints(cls, app: FastAPI) -> None:
        tags: list[str | Enum] = cls.get_tags()

        # create
        cls.ROUTER.add_api_route(
            methods=["POST"],
            path=f"/{cls.prefix}",
            endpoint=cls.create(),
            response_model=getattr(cls, "Reader", cls.Table),  # type: ignore
            tags=tags,
            name=f"Create a {cls.__name__.lower()}",
        )

        # many
        cls.ROUTER.add_api_route(
            methods=["GET"],
            path=f"/{cls.prefix}",
            endpoint=cls.get_all(),
            response_model=list[getattr(cls, "Reader", cls.Table)],  # type: ignore
            tags=tags,
            name=f"Get all {tags[0]}",
        )

        # one
        cls.ROUTER.add_api_route(
            methods=["GET"],
            path=f"/{cls.prefix}/{{obj_id}}",
            endpoint=cls.get_one(),
            response_model=getattr(cls, "Reader", cls.Table),
            tags=tags,
            name=f"Get one {cls.__name__.lower()}",
        )

        # update
        cls.ROUTER.add_api_route(
            methods=["PATCH"],
            path=f"/{cls.prefix}/{{obj_id}}",
            endpoint=cls.update(),
            response_model=getattr(cls, "Reader", cls.Table),
            tags=tags,
            name=f"Update a {cls.__name__.lower()}",
        )

        # delete
        cls.ROUTER.add_api_route(
            methods=["DELETE"],
            path=f"/{cls.prefix}/{{obj_id}}",
            endpoint=cls.delete(),
            response_model=ConfirmationModel,
            tags=tags,
            name=f"Delete a {cls.__name__.lower()}",
        )

    @classmethod
    def seed(cls: type[Endpointer]) -> None:
        with Session(cls.engine) as session:
            for obj in cls.SEED_OBJS:
                create_obj = cls.Creator(**obj)
                db_obj = cls.Table.model_validate(create_obj)
                session.add(db_obj)
                session.commit()
                session.refresh(db_obj)
                # session.delete(db_obj)
                # session.commit()


class User(Endpointer):
    prefix = "users"

    SEED_OBJS = ({"name": "User1", "email": "foo@bar.com", "password": "12345"},)

    class Table(SQLModel, table=True):
        __tablename__ = "user"

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


class TaggedPost(Endpointer):
    prefix = "tagged_posts"

    SEED_OBJS = ({"tag_id": 1, "post_id": 1},)

    class Table(SQLModel, table=True):
        __tablename__ = "tagged_post"

        tag_id: int | None = TAG_ID_PRIMARY_FIELD
        post_id: int | None = POST_ID_PRIMARY_FIELD

    class Creator(SQLModel):
        tag_id: int
        post_id: int

    class Updater(SQLModel):
        tag_id: int | None = None
        post_id: int | None = None


    @classmethod
    def query_apply(  # type: ignore[override]
        cls,
        query: Any,
        tag_id: int | None = None,
        post_id: int | None = None,
    ) -> Any:
        if tag_id:
            query = query.where(cls.Table.tag_id == tag_id)
        if post_id:
            query = query.where(cls.Table.post_id == post_id)
        return query


    @classmethod
    def get_all(
        cls,
    ) -> Callable[
        [
            DefaultNamedArg(Session, "session"),
            NamedArg(dict[str, int | None], "pagination"),
            DefaultNamedArg(dict[str, str], "sort_"),
        ],
        list[Endpointer.Table],
    ]:
        def route(
            *,
            session: Session = Depends(cls.get_db),
            pagination: Pagination,
            sort_: SORT = sort_factory(cls.Table),
            tag_id: int | None = None,
            post_id: int | None = None,
        ) -> list[Endpointer.Table]:
            return cls._do_get_all(
                session,
                pagination,
                sort_,
                tag_id=tag_id,
                post_id=post_id
            )

        return route


    @classmethod
    def delete(
        cls,
    ) -> Callable[
        [
            DefaultNamedArg(Session, "session"),
            NamedArg(dict[str, int | None], "pagination"),
            DefaultNamedArg(dict[str, str], "sort_"),
        ],
        ConfirmationModel,
    ]:
        def route(
            *,
            session: Session = Depends(cls.get_db),
            tag_id: int,
            post_id: int,
        ) -> ConfirmationModel:
            tagged_post = session.exec(
                cls.select()
                .where(
                    cls.Table.tag_id == tag_id,
                    cls.Table.post_id == post_id
                )
            ).first()
            if not tagged_post:
                raise HTTPException(status_code=404, detail=f'Tagged post with {tag_id=} and {post_id=} not found.')
            session.delete(tagged_post)
            session.commit()
            return {'ok': True}
        return route

    @classmethod
    def include_endpoints(cls, app: FastAPI) -> None:
        tags: list[str | Enum] = cls.get_tags()

        # create
        cls.ROUTER.add_api_route(
            methods=["POST"],
            path=f"/{cls.prefix}",
            endpoint=cls.create(),
            response_model=getattr(cls, "Reader", cls.Table),  # type: ignore
            tags=tags,
            name=f"Create a {cls.__name__.lower()}",
        )

        # many
        cls.ROUTER.add_api_route(
            methods=["GET"],
            path=f"/{cls.prefix}",
            endpoint=cls.get_all(),
            response_model=list[getattr(cls, "Reader", cls.Table)],  # type: ignore
            tags=tags,
            name=f"Get all {tags[0]}",
        )

        # delete
        cls.ROUTER.add_api_route(
            methods=["DELETE"],
            path=f"/{cls.prefix}",
            endpoint=cls.delete(),
            response_model=ConfirmationModel,
            tags=tags,
            name=f"Delete a {cls.__name__.lower()}",
        )


class Tag(Endpointer):
    prefix = "tags"

    SEED_OBJS = ({"name": "Tag1"},)

    class Table(SQLModel, table=True):
        __tablename__ = "tag"

        id: int | None = ID_FIELD
        name: str | None

    class Creator(SQLModel):
        name: str

    class Updater(SQLModel):
        name: str | None = None


class Post(Endpointer):
    prefix = "posts"

    SEED_OBJS = ({"name": "Post1", "content": "Post1 content", "author": 1},)

    class Base(Endpointer.Table):
        id: int | None = ID_FIELD
        name: str | None
        content: str | None
        author: int | None = USER_ID_FIELD
        created_at: datetime | None = CREATED_AT_FIELD
        updated_at: datetime | None = UPDATED_AT_FIELD

    class Table(Base, table=True):
        __tablename__ = "post"

    class Creator(SQLModel):
        name: str
        content: str
        author: int

    class Updater(SQLModel):
        name: str | None = None
        content: str | None = None
        author: int | None = None

    class Reader(Base):
        tags: list[Tag.Table] = []

    @classmethod
    def obj_apply(cls, obj: Table | sqlalchemy.engine.row.Row[tuple[Table]], session: Session) -> Reader:  # type: ignore[override]
        print(obj)
        print(type(obj))
        if type(obj) is sqlalchemy.engine.row.Row:
            print('hello')
            obj = obj[0]
        else:
            print('no')
        tagged_posts = session.exec(
            select(TaggedPost.Table).where(TaggedPost.Table.post_id == obj.id),  # type: ignore
        ).all()
        print('x', tagged_posts)
        tags = [
            session.get(Tag.Table, tagged_post.tag_id) for tagged_post in tagged_posts
        ]
        reader_obj = cls.Reader(name=None, content=None, author=None)
        for field in obj.model_fields:
            setattr(reader_obj, field, getattr(obj, field))
        reader_obj.tags = tags
        return reader_obj

    T = TypeVar('T')

    @classmethod
    def query_apply(  # type: ignore[override]
        cls,
        query,
        *,
        session: Session,
        name: str | None = None,
        author: int | None = None,
        tags: str | None = None,
        earliest_created: datetime | None = None,
        latest_created: datetime | None = None,
        earliest_updated: datetime | None = None,
        latest_updated: datetime | None = None,
    ):
        # return query
        # # ignore passed in query, use our own
        other_tables = (TaggedPost.Table, User.Table)
        non_empty_other_tables = [
            session.exec(select(table)).first() is not None
            for table in other_tables
        ]
        query = select(cls.Table, *non_empty_other_tables)
        # print(name, author, tags, earliest_created, earliest_updated, latest_created, latest_updated)
        if name:
            query = query.where(cls.Table.name == name)
        if author:
            query = query.where(cls.Table.author == author)
        if tags:
            tag_ids = tags.split(",")
            for tag in tag_ids:
                query = query.where(
                    TaggedPost.Table.post_id == cls.Table.id,
                    TaggedPost.Table.tag_id == int(tag)
                )

        # TODO check that this actually filters correctly
        if earliest_created:
            query = query.where(cls.Table.created_at > earliest_created)  # type: ignore[operator]
        if latest_created:
            query = query.where(cls.Table.created_at < latest_created)  # type: ignore[operator]
        if earliest_updated:
            query = query.where(cls.Table.updated_at > earliest_updated)  # type: ignore[operator]
        if latest_updated:
            query = query.where(cls.Table.updated_at < earliest_updated)  # type: ignore[operator]
        print(query)
        return query

    @classmethod
    def get_all(
        cls,
    ) -> Callable[
        [
            DefaultNamedArg(Session, "session"),
            NamedArg(dict[str, int | None], "pagination"),
            DefaultNamedArg(dict[str, str], "sort_"),
        ],
        list[Endpointer.Table],
    ]:
        def route(
            *,
            session: Session = Depends(cls.get_db),
            pagination: Pagination,
            sort_: SORT = sort_factory(cls.Table),
            name: str | None = None,
            author: int | None = None,
            tags: str | None = None,
            earliest_created: datetime | None = None,
            latest_created: datetime | None = None,
            earliest_updated: datetime | None = None,
            latest_updated: datetime | None = None,
        ) -> list[Post.Reader]:
            return cls._do_get_all(
                session=session,
                pagination=pagination,
                sort_=sort_,
                name=name,
                author=author,
                tags=tags,
                earliest_created=earliest_created,
                latest_created=latest_created,
                earliest_updated=earliest_updated,
                latest_updated=latest_updated,
            )

        return route


class Comment(Endpointer):
    prefix = "comments"

    SEED_OBJS = ()

    class Table(SQLModel, table=True):
        __tablename__ = "comment"

        id: int | None = ID_FIELD
        content: str | None
        post_id: int | None = POST_ID_FIELD
        author: int | None = USER_ID_FIELD
        created_at: datetime | None = CREATED_AT_FIELD
        updated_at: datetime | None = UPDATED_AT_FIELD

    class Creator(SQLModel):
        content: str
        author: int
        post_id: int

    class Updater(SQLModel):
        content: str | None = None
        author: int | None = None

    @classmethod
    def query_apply(  # type: ignore[override]
        cls,
        query: Any,
        post_id: int | None = None,
    ) -> Any:
        if post_id:
            query = query.where(cls.Table.post_id == post_id)
        return query


    @classmethod
    def get_all(
        cls,
    ) -> Callable[
        [
            DefaultNamedArg(Session, "session"),
            NamedArg(dict[str, int | None], "pagination"),
            DefaultNamedArg(dict[str, str], "sort_"),
        ],
        list[Endpointer.Table],
    ]:
        def route(
            *,
            session: Session = Depends(cls.get_db),
            pagination: Pagination,
            sort_: SORT = sort_factory(cls.Table),
            post_id: int | None = None,
        ) -> list[Endpointer.Table]:
            return cls._do_get_all(
                session,
                pagination,
                sort_,
                post_id=post_id,
            )

        return route
