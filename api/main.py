from __future__ import annotations

import textwrap

from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from sqlmodel import Session, select


# from .models import MODELS, User, UserCreate, Tag, TagCreate, Post, PostCreate, Comment, CommentCreate, Index, create_all, get_db
from .models import User, Tag, Post, TaggedPost, Comment, create_all, get_db, Endpointed

app = FastAPI()

User.include_endpoints(app)
Tag.include_endpoints(app)
Post.include_endpoints(app)
TaggedPost.include_endpoints(app)
Comment.include_endpoints(app)

app.include_router(Endpointed.ROUTER)


# # # generate CRUD routes
# for model_info in MODELS.values():
# router = SQLAlchemyCRUDRouter(
#     schema=User.Table,
#     create_schema=User.Creator,
#     update_schema=User.Creator,
#     db_model=User.Table,
#     db=get_db,
#     prefix=User.PREFIX,
#     tags=User.get_tags()
# )
# app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    create_all(wipe_old=True, do_seed=True)


# @app.get('/users/', tags=['Users'])
# def blegh(
#     *,
#     session: Session = Depends(get_db),
#     pagination: Pagination
# ) -> list[User]:
#     return session.exec(
#         select(User)
#         .offset(pagination.offset)
#         .limit(pagination.limit)
#     ).all()


# @app.get('/users/{user_id}', response_model=User, tags=['Users'])
# def get_user(
#     *,
#     session: Session = Depends(get_db),
#     user_id: int
# ) -> User:
#     if not (user := session.get(User, user_id)):
#         raise ElemNotFoundException('User', user_id)
#     return user


# @app.patch('/users/{user_id}', response_model=User, tags=['Users'])
# def update_user(
#     *,
#     session: Session = Depends(get_db),
#     user_id: int,
#     user: UserCreate
# ) -> User:
#     if not (user_db := session.get(User, user_id)):
#         raise ElemNotFoundException('User', user_id)
#     user_data = user.dict(exclude_unset=True)
#     for k, v in user_data.items():
#         setattr(user_db, k, v)
#     session.add(user_db)
#     session.commit()
#     session.refresh(user_db)
#     return user_db


# @app.delete('/users/{user_id}', tags=['Users'])
# def delete_user(
#     *,
#     session: Session = Depends(get_db),
#     user_id: int
# ) -> Index:
#     if not (user := session.get(User, user_id)):
#         raise ElemNotFoundException('User', user_id)
#     session.delete(user)
#     session.commit()
#     return {'ok': True}


# @app.get('/tags/', response_model=list[Tag], tags=['Tags'])
# def get_tags(
#     *,
#     session: Session = Depends(get_db),
#     pagination: Pagination
# ) -> list[Tag]:
#     return session.exec(
#         select(Tag)
#         .offset(pagination.offset)
#         .limit(pagination.limit)
#     ).all()


# @app.get('/users/{user_id}', response_model=User, tags=['Users'])
# def get_user(
#     *,
#     session: Session = Depends(get_db),
#     user_id: int
# ) -> User:
#     if not (user := session.get(User, user_id)):
#         raise ElemNotFoundException('User', user_id)
#     return user


# @app.patch('/users/{user_id}', response_model=User, tags=['Users'])
# def update_user(
#     *,
#     session: Session = Depends(get_db),
#     user_id: int,
#     user: UserCreate
# ) -> User:
#     if not (user_db := session.get(User, user_id)):
#         raise ElemNotFoundException('User', user_id)
#     user_data = user.dict(exclude_unset=True)
#     for k, v in user_data.items():
#         setattr(user_db, k, v)
#     session.add(user_db)
#     session.commit()
#     session.refresh(user_db)
#     return user_db


# @app.delete('/users/{user_id}', tags=['Users'])
# def delete_user(
#     *,
#     session: Session = Depends(get_db),
#     user_id: int
# ) -> Index:
#     if not (user := session.get(User, user_id)):
#         raise ElemNotFoundException('User', user_id)
#     session.delete(user)
#     session.commit()
#     return {'ok': True}

# # @app.get(
# #     "/tags/{item_id}/posts",
#     response_model=list[Index],
#     tags=["Tags"],
# )
# def get_posts_with_tag(
#     *,
#     session: Session = Depends(get_db),
#     pagination: Pagination,
#     item_id: int,
# ) -> list[int]:
#     if not session.get(Tag, item_id):
#         msg = "Category"
#         raise ElemNotFoundException(msg, item_id)

#     return session.exec(
#         select(Thread.id or 0)
#         .where(Thread.category_id == item_id)
#         .offset(pagination["skip"])
#         .limit(pagination["limit"]),
#     ).all()


# @app.get("/threads/{item_id}/posts", response_model=list[Index], tags=["Threads"])
# def get_thread_post_ids(
#     *,
#     session: Session = Depends(get_db),
#     pagination: Pagination,
#     item_id: int,
# ) -> list[int]:
#     if not session.get(Thread, item_id):
#         msg = "Thread"
#         raise ElemNotFoundException(msg, item_id)

#     return session.exec(
#         select(Post.id or 0)
#         .where(Post.thread_id == item_id)
#         .offset(pagination["skip"])
#         .limit(pagination["limit"]),
#     ).all()


endpoint_str = textwrap.dedent(
    """

    Endpoints: Special
    ------------------

    GET /categories/<category_id>/threads
        Get a list of a category's thread IDs.

    GET /threads/<thread_id>/posts
        Get a list of a thread's post IDs.


    Endpoints: Generic CRUDs supported
    ----------------------------------

    GET /<items> (?offset=0&limit=100)
        Get a list of items.

    POST /<items>
        Create an item.

    GET /<items>/<item_id>
        Get an item.

    UPDATE /<items>/<item_id>
        Update an item.

    DELETE /<items>
        Delete all items.

    DELETE /<items>/<item_id>
        Delete an item.
""",
).lstrip()


@app.get("/tldr", response_class=PlainTextResponse)
async def get_tldr_docs() -> str:
    return str(Post.Reader.schema())
    # return str(Post.Reader.__repr__())
    # return str(dir(app))
    lines_mixed_types = ["Objects", "-------", ""]
    for model in MODELS.values():
        schema = model.table.schema()
        lines_mixed_types.append(f'{schema["title"]}:  (/{model.prefix})')
        for property_name, property in schema["properties"].items():  # noqa: A001
            lines_mixed_types.append(
                {
                    "string": f'{" " * 4}{property_name}: {property["type"]}',
                    "is_readonly": property_name
                    not in model.creator.schema()["properties"],
                },
            )
        lines_mixed_types.append("\n")

    lines = []

    for line in lines_mixed_types:
        if not isinstance(line, dict):
            lines.append(line)
        elif not line["is_readonly"]:  #
            lines.append(line["string"])
        else:
            readonly_tag_index = len(max(lines_mixed_types, key=len)) + 2
            lines.append(f'{line["string"]: <{readonly_tag_index}}(read-only)')

    return "\n".join(lines) + "\n" + endpoint_str


if __name__ == "__main__":
    pass
