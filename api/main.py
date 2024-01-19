from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine

from .models import Endpointer
import uvicorn
import click

app = FastAPI()

Endpointer.init_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"msg": "Hello World"}


@click.command()
@click.option('--seed/--no-seed', default=False)
@click.option('--db-path', required=True)
@click.option('--db-echo/--no-db-echo', default=False)
@click.option('--db-wipe-on-start/--no-db-wipe-on-start', default=False)
def start(seed, db_path, db_echo, db_wipe_on_start):
    db = Path(db_path)
    engine = create_engine(f"sqlite:///{db}", echo=db_echo)
    if db_wipe_on_start:
        db.unlink(missing_ok=True)
    Endpointer.init(engine, do_seed=seed)
    uvicorn.run(app, port=8000)


if __name__ == "__main__":
    start()
