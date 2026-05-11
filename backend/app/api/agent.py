"""Agent ingestion endpoints — used by the Ghost CFO Windows agent.

POST /api/agent/ingest   — receive an encrypted financial snapshot
GET  /api/agent/status   — agent health check (agent polls this)

Auth: X-Agent-Key header (per-company API key stored in evolution_agents table).
"""
from __future__ import annotations

import base64
import json
import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.evolution_agent import EvolutionAgent
from app.models.report import Report
from app.tasks.generate_report import generate_report_from_agent

log = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_agent(api_key: str, db: Session) -> EvolutionAgent:
    agent = db.execute(
        select(EvolutionAgent).where(
            EvolutionAgent.api_key == api_key,
            EvolutionAgent.active == True,  # noqa: E712
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive agent key",
        )
    return agent


def _decrypt_envelope(payload_b64: str, key: str) -> dict:
    """Decrypt AES-256-GCM envelope produced by agent/sync/encryptor.py."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    try:
        envelope = json.loads(base64.b64decode(payload_b64))
        key_bytes = key.encode()
        if len(key_bytes) != 32:
            key_bytes = key_bytes.ljust(32, b"\x00")[:32]

        nonce = base64.b64decode(envelope["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])
        tag = base64.b64decode(envelope["tag"])

        aesgcm = AESGCM(key_bytes)
        plaintext = aesgcm.decrypt(nonce, ciphertext + tag, None)
        return json.loads(plaintext)
    except Exception as exc:
        log.warning("Payload decryption failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payload decryption failed — check encryption key",
        ) from exc


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    payload: str  # base64-encoded AES-GCM envelope


class IngestResponse(BaseModel):
    accepted: bool
    report_task_id: str | None = None
    message: str


class StatusResponse(BaseModel):
    agent_id: str
    company_id: str
    company_name: str
    last_sync_at: datetime | None
    last_sync_status: str | None
    active: bool
    # Non-null when a bookkeeper has submitted payroll files and is waiting
    # for accounting data from this agent to complete the report.
    pending_sync_month: int | None = None
    pending_sync_year: int | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/ingest", response_model=IngestResponse)
def ingest(
    body: IngestRequest,
    x_agent_key: str = Header(alias="X-Agent-Key"),
    db: Session = Depends(get_db),
) -> IngestResponse:
    """Receive an encrypted financial snapshot from a client's Evolution agent."""
    from sqlalchemy import select as sa_select
    from app.models.upload import Upload

    agent = _get_agent(x_agent_key, db)
    company = agent.company

    log.info("Ingest request from company '%s' (agent %s)", company.name, agent.id)

    encryption_key = settings.agent_encryption_key
    data = _decrypt_envelope(body.payload, encryption_key)

    period_month: int = data.get("period_month", 0)
    period_year: int = data.get("period_year", 0)

    if not period_month or not period_year:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payload missing period_month / period_year",
        )

    # Check for a payroll-only upload that is waiting for this accounting data.
    # This is set when an Evolution client's bookkeeper uploads payroll files
    # via the portal and clicks "Generate Report".
    waiting_upload = db.execute(
        sa_select(Upload).where(
            Upload.company_id == company.id,
            Upload.period_month == period_month,
            Upload.period_year == period_year,
            Upload.status == "pending",
        )
    ).scalar_one_or_none()

    if waiting_upload:
        log.info(
            "Found waiting payroll upload %s — merging with agent accounting data",
            waiting_upload.id,
        )
        # Inject payroll file paths into the agent data so the pipeline can parse them
        data["payroll_upload_id"] = str(waiting_upload.id)
        waiting_upload.status = "processing"

    # Clear the pending sync request now that the data has arrived
    agent.pending_sync_month = None
    agent.pending_sync_year = None
    agent.last_sync_at = datetime.now(timezone.utc)
    agent.last_sync_status = "accepted"

    if waiting_upload:
        waiting_upload.status = "processing"

    db.commit()

    task = generate_report_from_agent.delay(
        company_id=str(company.id),
        metrics_data=data,
        period_month=period_month,
        period_year=period_year,
    )

    log.info(
        "Payload accepted for %s %d/%d — task %s",
        company.name, period_month, period_year, task.id,
    )
    return IngestResponse(
        accepted=True,
        report_task_id=task.id,
        message=f"Snapshot accepted for {period_month}/{period_year}. Report generation queued.",
    )


@router.get("/status", response_model=StatusResponse)
def agent_status(
    x_agent_key: str = Header(alias="X-Agent-Key"),
    db: Session = Depends(get_db),
) -> StatusResponse:
    """Health check + pending sync check.

    The agent polls this endpoint. If pending_sync_month/year are set,
    the agent must run a sync for that period immediately.
    """
    agent = _get_agent(x_agent_key, db)
    return StatusResponse(
        agent_id=str(agent.id),
        company_id=str(agent.company_id),
        company_name=agent.company.name,
        last_sync_at=agent.last_sync_at,
        last_sync_status=agent.last_sync_status,
        active=agent.active,
        pending_sync_month=agent.pending_sync_month,
        pending_sync_year=agent.pending_sync_year,
    )


@router.post("/heartbeat", status_code=204)
def heartbeat(
    x_agent_key: str = Header(alias="X-Agent-Key"),
    db: Session = Depends(get_db),
) -> None:
    """Lightweight liveness ping — agent calls this every 5 minutes.

    Updates last_heartbeat_at so the operator dashboard can show whether
    the agent process is running, independently of the monthly data sync.
    """
    agent = _get_agent(x_agent_key, db)
    agent.last_heartbeat_at = datetime.now(timezone.utc)
    db.commit()


# ---------------------------------------------------------------------------
# Admin endpoints (JWT-authenticated — Numbers10 staff only)
# ---------------------------------------------------------------------------

from app.api.deps import require_admin  # noqa: E402


class CreateAgentRequest(BaseModel):
    company_id: str
    server_name: str | None = None
    db_name: str | None = None
    db_username: str | None = None
    db_password: str | None = None


class AgentDetail(BaseModel):
    id: str
    company_id: str
    company_name: str
    api_key: str
    encryption_key: str
    server_name: str | None
    db_name: str | None
    db_username: str | None
    db_password: str | None
    last_sync_at: datetime | None
    last_sync_status: str | None
    active: bool


def _agent_detail(a: EvolutionAgent) -> AgentDetail:
    return AgentDetail(
        id=str(a.id),
        company_id=str(a.company_id),
        company_name=a.company.name,
        api_key=a.api_key,
        encryption_key=settings.agent_encryption_key,
        server_name=a.server_name,
        db_name=a.db_name,
        db_username=a.db_username,
        db_password=a.db_password,
        last_sync_at=a.last_sync_at,
        last_sync_status=a.last_sync_status,
        active=a.active,
    )


@router.get("/agents", response_model=list[AgentDetail])
def list_agents(
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> list[AgentDetail]:
    agents = db.execute(select(EvolutionAgent)).scalars().all()
    return [_agent_detail(a) for a in agents]


@router.post("/agents", response_model=AgentDetail, status_code=201)
def create_agent(
    body: CreateAgentRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> AgentDetail:
    """Provision a new agent for an Evolution client (generates a fresh API key)."""
    import uuid
    api_key = secrets.token_urlsafe(32)
    agent = EvolutionAgent(
        company_id=uuid.UUID(body.company_id),
        api_key=api_key,
        server_name=body.server_name,
        db_name=body.db_name,
        db_username=body.db_username,
        db_password=body.db_password,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return _agent_detail(agent)


@router.patch("/agents/{agent_id}", response_model=AgentDetail)
def update_agent(
    agent_id: str,
    body: CreateAgentRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> AgentDetail:
    """Update SQL connection details for an existing agent."""
    import uuid
    agent = db.get(EvolutionAgent, uuid.UUID(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if body.server_name is not None:
        agent.server_name = body.server_name
    if body.db_name is not None:
        agent.db_name = body.db_name
    if body.db_username is not None:
        agent.db_username = body.db_username
    if body.db_password is not None:
        agent.db_password = body.db_password
    db.commit()
    db.refresh(agent)
    return _agent_detail(agent)


class ServiceCheck(BaseModel):
    ok: bool
    message: str


class SystemStatus(BaseModel):
    database: ServiceCheck
    redis: ServiceCheck
    payfast: ServiceCheck
    resend: ServiceCheck
    openrouter: ServiceCheck
    agent_key: ServiceCheck


@router.get("/system-status", response_model=SystemStatus)
def system_status(
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> SystemStatus:
    """System connectivity and configuration status for admin dashboard."""
    import sqlalchemy as _sa

    # Database
    try:
        db.execute(_sa.text("SELECT 1"))
        db_check = ServiceCheck(ok=True, message="Connected")
    except Exception as exc:
        db_check = ServiceCheck(ok=False, message=str(exc)[:120])

    # Redis
    try:
        import redis as _redis
        r = _redis.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        redis_check = ServiceCheck(ok=True, message="Connected")
    except Exception as exc:
        redis_check = ServiceCheck(ok=False, message=str(exc)[:120])

    def cfg(ok: bool, label: str) -> ServiceCheck:
        return ServiceCheck(ok=ok, message="Configured" if ok else f"{label} not configured")

    return SystemStatus(
        database=db_check,
        redis=redis_check,
        payfast=cfg(bool(settings.payfast_merchant_id and settings.payfast_merchant_key), "PayFast credentials"),
        resend=cfg(bool(settings.resend_api_key), "RESEND_API_KEY"),
        openrouter=cfg(bool(settings.openrouter_api_key), "OPENROUTER_API_KEY"),
        agent_key=cfg(settings.agent_encryption_key not in ("", "change-me-32-bytes"), "AGENT_ENCRYPTION_KEY"),
    )


@router.post("/agents/{agent_id}/reactivate", response_model=AgentDetail)
def reactivate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> AgentDetail:
    """Re-activate a previously deactivated agent."""
    import uuid
    agent = db.get(EvolutionAgent, uuid.UUID(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.active = True
    db.commit()
    db.refresh(agent)
    return _agent_detail(agent)


@router.delete("/agents/{agent_id}")
def deactivate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> None:
    """Deactivate (soft delete) an agent."""
    import uuid
    agent = db.get(EvolutionAgent, uuid.UUID(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.active = False
    db.commit()
    # Return None for 204 No Content (no response body)
    return None