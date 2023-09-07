from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from sqlmodel import Session, select
import textwrap

# from .models import *

from .models import MODELS, Category, Index, Post, Thread, create_all, get_db
# from .tldr import tldr_docs

app = FastAPI()


# generate CRUD routes
for model_info in MODELS.values():
    router = SQLAlchemyCRUDRouter(
        schema=model_info.table,
        create_schema=model_info.creator,
        db_model=model_info.table,
        db=get_db,
        prefix=model_info.prefix,
    )
    app.include_router(router)


def pagination(skip: int = 0, limit: int | None = None) -> dict[str, int | None]:
    return {"skip": skip, "limit": limit}


Pagination = Annotated[dict[str, int | None], Depends(pagination)]


class ElemNotFoundException(HTTPException):
    def __init__(self: ElemNotFoundException, elem: str, n: int) -> None:
        self.elem = elem
        self.n = n

    def __str__(self: ElemNotFoundException) -> str:
        return f"{self.elem} #{self.n} not found"


@app.on_event("startup")
def on_startup() -> None:
    create_all(wipe_old=True, do_seed=True)


@app.get(
    "/categories/{item_id}/threads",
    response_model=list[Index],
    tags=["Categories"],
)
def get_category_thread_ids(
    *,
    session: Session = Depends(get_db),
    pagination: Pagination,
    item_id: int,
) -> list[int]:
    if not session.get(Category, item_id):
        msg = "Category"
        raise ElemNotFoundException(msg, item_id)

    return session.exec(
        select(Thread.id or 0)
        .where(Thread.category_id == item_id)
        .offset(pagination["skip"])
        .limit(pagination["limit"]),
    ).all()


@app.get("/threads/{item_id}/posts", response_model=list[Index], tags=["Threads"])
def get_thread_post_ids(
    *,
    session: Session = Depends(get_db),
    pagination: Pagination,
    item_id: int,
) -> list[int]:
    if not session.get(Thread, item_id):
        msg = "Thread"
        raise ElemNotFoundException(msg, item_id)

    return session.exec(
        select(Post.id or 0)
        .where(Post.thread_id == item_id)
        .offset(pagination["skip"])
        .limit(pagination["limit"]),
    ).all()


endpoint_str = textwrap.dedent('''

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
''').lstrip()

print(dir(app))
print(app.openapi_tags)


@app.get("/tldr", response_class=PlainTextResponse)
async def get_tldr_docs() -> str:
    return str(dir(app))
    # return str(app.openapi())
    lines_mixed_types = [
        'Objects',
        '-------',
        ''
    ]
    for model_name, model in MODELS.items():
        schema = model.table.schema()
        lines_mixed_types.append(f'{schema["title"]}:  (/{model.prefix})')
        for property_name, property in schema['properties'].items():
            lines_mixed_types.append({
                'string': f'{" " * 4}{property_name}: {property["type"]}',
                'is_readonly': property_name not in model.creator.schema()['properties']
            })
        lines_mixed_types.append('\n')

    lines = []

    for line in lines_mixed_types:
        if not isinstance(line, dict): 
            lines.append(line)
        elif not line['is_readonly']:   # 
            lines.append(line['string'])
        else:
            readonly_tag_index = len(max(lines_mixed_types, key=len)) + 2
            lines.append(f'{line["string"]: <{readonly_tag_index}}(read-only)')

    return '\n'.join(lines) + '\n' + endpoint_str


    # return tldr_docs


if __name__ == "__main__":
    pass
