from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router, ws_router
from app.core.config import settings
from app.db.init_db import init_db
from app.services.realtime.runtime import stream_processor

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

media_root = Path(__file__).resolve().parents[1] / "data"
media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_root)), name="media")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    stream_processor.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stream_processor.stop()


app.include_router(api_router)
app.include_router(ws_router)
