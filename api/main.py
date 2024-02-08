from __future__ import annotations

from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine

from .models import Endpointer
from . import seeder
import uvicorn
import asyncclick as click
import asyncio


async def do_seed(server):
    while not server.started:
        await asyncio.sleep(1)
    await seeder.main()


@click.command()
@click.option('--seed/--no-seed', default=False)
@click.option('--db-path', required=True)
@click.option('--db-echo/--no-db-echo', default=False)
@click.option('--db-wipe-on-start/--no-db-wipe-on-start', default=False)
async def start(seed, db_path, db_echo, db_wipe_on_start):
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Endpointer.init_app(app)


    db = Path(db_path)
    engine = create_engine(f"sqlite:///{db}", echo=db_echo)
    if db_wipe_on_start:
        db.unlink(missing_ok=True)
    Endpointer.init(engine, do_seed=False)
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    if seed:
        asyncio.create_task(do_seed(server))
    await server.serve()


if __name__ == "__main__":
    start()
