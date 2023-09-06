from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from prometheus_fastapi_instrumentator import Instrumentator
from sqlmodel import Session, select

from .models import MODELS, Category, Index, Post, Thread, create_all, get_db
from .tldr import tldr_docs

app = FastAPI()

Instrumentator().instrument(app).expose(app, include_in_schema=True, should_gzip=True)


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


@app.get("/tldr", response_class=PlainTextResponse)
async def get_tldr_docs() -> str:
    return tldr_docs


if __name__ == "__main__":
    pass
