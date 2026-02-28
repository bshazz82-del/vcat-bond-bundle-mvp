from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import api, models
from .db import engine

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="VCAT Bond Bundle API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api.router)

    @app.on_event("startup")
    def on_startup() -> None:
        models.Base.metadata.create_all(bind=engine)
        logger.info("DB ready.")
    return app

app = create_app()
