from typing import Annotated
from sqlmodel import select, Session
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    MODELS,
    get_db,
    create_all,
    Index,
    Category,
    Thread,
    Post,
    UserCreate,
    UserBase,
    User,
)

from .tldr import tldr_docs


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hello world


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


def pagination(skip: int = 0, limit: int | None = None):
    return {"skip": skip, "limit": limit}


Pagination = Annotated[dict, Depends(pagination)]


class ElemNotFoundException(HTTPException):
    def __init__(self, elem, n):
        self.elem = elem
        self.n = n

    def __str__(self):
        return f"{self.elem} #{self.n} not found"


@app.on_event("startup")
def on_startup():
    create_all(wipe_old=True, do_seed=True)


@app.get(
    "/categories/{item_id}/threads", response_model=list[Index], tags=["Categories"]
)
def get_category_thread_ids(
    *, session: Session = Depends(get_db), pagination: Pagination, item_id: int
):
    if session.get(Category, item_id):
        return session.exec(
            select(Thread)
            .where(Thread.category_id == item_id)
            .offset(pagination["skip"])
            .limit(pagination["limit"])
        ).all()
    else:
        raise ElemNotFoundException("Category", item_id)


@app.get("/threads/{item_id}/posts", response_model=list[Index], tags=["Threads"])
def get_thread_post_ids(
    *, session: Session = Depends(get_db), pagination: Pagination, item_id: int
):
    if session.get(Thread, item_id):
        return session.exec(
            select(Post)
            .where(Post.thread_id == item_id)
            .offset(pagination["skip"])
            .limit(pagination["limit"])
        ).all()
    else:
        raise ElemNotFoundException("Thread", item_id)


@app.get("/tldr", response_class=PlainTextResponse)
async def get_tldr_docs():
    return tldr_docs


@app.post("/users", response_model=UserBase, tags=["Users"])
async def create_user(user_data: UserCreate, session: Session = Depends(get_db)):
    existing_user = session.query(User).filter_by(email=user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")

    try:
        new_user = User(**user_data.dict())

        new_user.password = user_data.password

        session.add(new_user)
        session.commit()

        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
