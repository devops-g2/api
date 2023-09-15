from __future__ import annotations



import textwrap

from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware

import warnings
from sqlalchemy.exc import SAWarning
warnings.filterwarnings("ignore", category=SAWarning)


# from .models import MODELS, User, UserCreate, Tag, TagCreate, Post, PostCreate, Comment, CommentCreate, Index, create_all, get_db
from .models import User, Tag, Post, TaggedPost, Comment, create_all, get_db, Endpointed


app = FastAPI()

User.include_endpoints(app)
Tag.include_endpoints(app)
Post.include_endpoints(app)
TaggedPost.include_endpoints(app)
Comment.include_endpoints(app)

app.include_router(Endpointed.ROUTER)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)


@app.on_event("startup")
def on_startup() -> None:
    create_all(wipe_old=True, do_seed=True)


@app.get('/')
async def root():
    return {'msg': 'Hello World'}


# TODO add uvicorn run
if __name__ == "__main__":
    pass
