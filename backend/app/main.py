"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import agent, auth, companies, payments, reports, uploads, users
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("ghostcfo.startup", env=settings.app_env, version=__version__)
    yield
    log.info("ghostcfo.shutdown")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Ghost CFO — AI financial narrative engine for SA SMBs.",
    lifespan=lifespan,
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"]
    if settings.app_env == "development"
    else [settings.base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(payments.router)
app.include_router(users.router)
app.include_router(uploads.router)
app.include_router(reports.router)
app.include_router(agent.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "env": settings.app_env}


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "tagline": "AI CFO for South African SMBs",
        "powered_by": "Numbers10 Technology Solutions",
    }
