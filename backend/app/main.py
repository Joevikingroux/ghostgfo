"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import admin_overview, agent, auth, companies, payments, reports, uploads, users
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env == "production":
        if settings.secret_key in ("", "change-me"):
            raise SystemExit("FATAL: SECRET_KEY is not set. Configure it in .env before starting.")
        if settings.agent_encryption_key in ("", "change-me-32-bytes"):
            raise SystemExit("FATAL: AGENT_ENCRYPTION_KEY is not set. Configure it in .env before starting.")
        if settings.payfast_sandbox:
            raise SystemExit("FATAL: PAYFAST_SANDBOX=True in production. Set PAYFAST_SANDBOX=False in .env.")
    log.info("ghostcfo.startup", env=settings.app_env, version=__version__)
    yield
    log.info("ghostcfo.shutdown")


_is_prod = settings.app_env == "production"

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Ghost CFO — AI financial narrative engine for SA SMBs.",
    lifespan=lifespan,
    root_path="/api",
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
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
app.include_router(admin_overview.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
