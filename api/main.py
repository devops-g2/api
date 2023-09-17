from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine

from .models import Endpointer

app = FastAPI()

Endpointer.init_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DB = Path("forum.db")

# prod
ENGINE = create_engine(f"sqlite:///{DB}")

# echo SQL statements sent; useful for debugging


@app.on_event("startup")
def on_startup() -> None:
    DB.unlink(missing_ok=True)
    Endpointer.init(ENGINE, do_seed=True)


@app.get("/")
async def root() -> dict[str, str]:
    return {"msg": "Hello World"}


if __name__ == "__main__":
    pass
