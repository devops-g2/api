from __future__ import annotations



import textwrap
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from sqlmodel import Session, select, create_engine
from fastapi.middleware.cors import CORSMiddleware

import warnings
from sqlalchemy.exc import SAWarning
warnings.filterwarnings("ignore", category=SAWarning)


# from .models import MODELS, User, UserCreate, Tag, TagCreate, Post, PostCreate, Comment, CommentCreate, Index, create_all, get_db
from .models import User, Tag, Post, TaggedPost, Comment, Endpointer


app = FastAPI()

User.include_endpoints(app)
Tag.include_endpoints(app)
Post.include_endpoints(app)
TaggedPost.include_endpoints(app)
Comment.include_endpoints(app)

app.include_router(Endpointer.ROUTER)

app.add_middleware(
   CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)


DB = Path('forum.db')
ENGINE = create_engine(f'sqlite:///{DB}')


@app.on_event("startup")
def on_startup() -> None:
    DB.unlink(missing_ok=True)
    Endpointer.init(ENGINE)

@app.get('/')
async def root():
    return {'msg': 'Hello World'}


# TODO add uvicorn run
if __name__ == "__main__":
    pass
