from __future__ import annotations



import textwrap
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from sqlmodel import Session, select, create_engine
from fastapi.middleware.cors import CORSMiddleware

from .models import Endpointer


app = FastAPI()

Endpointer.init_app(app)

app.add_middleware(
   CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)


DB = Path('forum.db')

# prod
ENGINE = create_engine(f'sqlite:///{DB}')

# echo SQL statements sent; useful for debugging
# ENGINE = create_engine(f'sqlite:///{DB}', echo=True)


@app.on_event("startup")
def on_startup() -> None:
    DB.unlink(missing_ok=True)
    Endpointer.init(ENGINE, do_seed=True)

@app.get('/')
async def root():
    return {'msg': 'Hello World'}


# TODO add uvicorn run
if __name__ == "__main__":
    pass
