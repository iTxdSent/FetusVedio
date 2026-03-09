from fastapi import APIRouter

from app.api.routes import auth, history, patients, stream, system
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_prefix)
ws_router = APIRouter()

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(system.router, tags=["system"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(stream.router, tags=["stream"])
api_router.include_router(history.router, tags=["history"])
ws_router.include_router(stream.ws_router, tags=["stream"])
