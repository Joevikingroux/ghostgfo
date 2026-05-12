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
from pydantic import BaseModel, Field
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

def _derive_agent_key(global_key: str, agent_id: str) -> bytes:
    """Derive a per-agent 32-byte AES key using HKDF-SHA256."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    key_bytes = global_key.encode()
    if len(key_bytes) != 32:
        key_bytes = key_bytes.ljust(32, b"\x00")[:32]
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=agent_id.encode()).derive(key_bytes)


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
        key_bytes = key.encode() if isinstance(key, str) else key
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

class ForceSyncRequest(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2035)


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

    derived_key = _derive_agent_key(settings.agent_encryption_key, str(agent.id))
    data = _decrypt_envelope(body.payload, derived_key)

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


class HeartbeatBody(BaseModel):
    sql_ok: bool | None = None


@router.post("/heartbeat", status_code=204, response_model=None)
def heartbeat(
    x_agent_key: str = Header(alias="X-Agent-Key"),
    body: HeartbeatBody | None = None,
    db: Session = Depends(get_db),
):
    """Lightweight liveness ping — agent calls this every 5 minutes.

    Accepts an optional JSON body with sql_ok to report SQL connection health.
    """
    agent = _get_agent(x_agent_key, db)
    agent.last_heartbeat_at = datetime.now(timezone.utc)
    if body and body.sql_ok is not None:
        agent.sql_connection_ok = body.sql_ok
    db.commit()


# ---------------------------------------------------------------------------
# Company-scoped endpoints (JWT-authenticated — any logged-in user)
# ---------------------------------------------------------------------------

from app.api.deps import get_current_user, require_admin, require_staff  # noqa: E402
from app.models.user import User  # noqa: E402


class CompanyAgentStatus(BaseModel):
    has_agent: bool
    agent_id: str | None = None
    connected: bool = False
    sql_ok: bool | None = None
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    server_name: str | None = None
    pending_sync_month: int | None = None
    pending_sync_year: int | None = None


@router.get("/company-status", response_model=CompanyAgentStatus)
def company_agent_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyAgentStatus:
    """Return the Evolution agent status for the current user's company.

    Returns has_agent=False if no active agent exists (e.g. Partner mode).
    """
    if not user.company_id:
        return CompanyAgentStatus(has_agent=False)

    agent = db.execute(
        select(EvolutionAgent).where(
            EvolutionAgent.company_id == user.company_id,
            EvolutionAgent.active == True,  # noqa: E712
        )
    ).scalar_one_or_none()

    if not agent:
        return CompanyAgentStatus(has_agent=False)

    now = datetime.now(timezone.utc)
    connected = False
    if agent.last_heartbeat_at:
        diff = (now - agent.last_heartbeat_at).total_seconds()
        connected = diff <= 12 * 60  # 12-minute grace (5-min interval + buffer)

    return CompanyAgentStatus(
        has_agent=True,
        agent_id=str(agent.id),
        connected=connected,
        sql_ok=agent.sql_connection_ok,
        last_sync_at=agent.last_sync_at,
        last_sync_status=agent.last_sync_status,
        server_name=agent.server_name,
        pending_sync_month=agent.pending_sync_month,
        pending_sync_year=agent.pending_sync_year,
    )


@router.post("/company-sync")
def company_request_sync(
    body: ForceSyncRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Queue an on-demand sync for the current user's company agent.

    The agent will pick this up on its next 5-minute poll and run the sync.
    Accessible to owners and bookkeepers — no admin role required.
    """
    if not user.company_id:
        raise HTTPException(status_code=400, detail="No company associated with your account")

    agent = db.execute(
        select(EvolutionAgent).where(
            EvolutionAgent.company_id == user.company_id,
            EvolutionAgent.active == True,  # noqa: E712
        )
    ).scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="No active Evolution agent for your company")

    agent.pending_sync_month = body.month
    agent.pending_sync_year = body.year
    db.commit()
    log.info(
        "Company sync queued by user %s: %02d/%d",
        user.id, body.month, body.year,
    )
    return {"ok": True, "queued_month": body.month, "queued_year": body.year}


# ---------------------------------------------------------------------------
# Admin endpoints (JWT-authenticated — Numbers10 staff only)
# ---------------------------------------------------------------------------


class CreateAgentRequest(BaseModel):
    company_id: str
    server_name: str | None = None
    db_name: str | None = None


class AgentDetail(BaseModel):
    id: str
    company_id: str
    company_name: str
    server_name: str | None
    db_name: str | None
    last_sync_at: datetime | None
    last_sync_status: str | None
    active: bool


class AgentCreatedDetail(AgentDetail):
    """Returned only on agent creation — credentials are not shown again after this."""
    api_key: str
    encryption_key: str


def _agent_detail(a: EvolutionAgent) -> AgentDetail:
    return AgentDetail(
        id=str(a.id),
        company_id=str(a.company_id),
        company_name=a.company.name,
        server_name=a.server_name,
        db_name=a.db_name,
        last_sync_at=a.last_sync_at,
        last_sync_status=a.last_sync_status,
        active=a.active,
    )


@router.get("/agents", response_model=list[AgentDetail])
def list_agents(
    db: Session = Depends(get_db),
    _: object = Depends(require_staff),
) -> list[AgentDetail]:
    agents = db.execute(select(EvolutionAgent)).scalars().all()
    return [_agent_detail(a) for a in agents]


@router.post("/agents", response_model=AgentCreatedDetail, status_code=201)
def create_agent(
    body: CreateAgentRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_staff),
) -> AgentCreatedDetail:
    """Provision a new agent. Returns API key + AES key once — not retrievable again."""
    import uuid
    api_key = secrets.token_urlsafe(32)
    agent = EvolutionAgent(
        company_id=uuid.UUID(body.company_id),
        api_key=api_key,
        server_name=body.server_name,
        db_name=body.db_name,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    detail = _agent_detail(agent)
    return AgentCreatedDetail(
        **detail.model_dump(),
        api_key=api_key,
        encryption_key=settings.agent_encryption_key,
    )


@router.patch("/agents/{agent_id}", response_model=AgentDetail)
def update_agent(
    agent_id: str,
    body: CreateAgentRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_staff),
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
    _: object = Depends(require_staff),
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
    _: object = Depends(require_staff),
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


@router.post("/agents/{agent_id}/force-sync")
def force_sync_agent(
    agent_id: str,
    body: ForceSyncRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_staff),
) -> dict:
    """Queue an on-demand sync for a specific period.

    Sets pending_sync_month/year on the agent record. The agent's 5-minute
    poll task will pick this up and run the sync within 5 minutes.
    """
    import uuid
    agent = db.get(EvolutionAgent, uuid.UUID(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.pending_sync_month = body.month
    agent.pending_sync_year = body.year
    db.commit()
    log.info(
        "Force sync queued for agent %s: %02d/%d",
        agent_id, body.month, body.year,
    )
    return {"ok": True, "queued_month": body.month, "queued_year": body.year}


@router.post("/agents/{agent_id}/deactivate", response_model=AgentDetail)
def deactivate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_staff),
) -> AgentDetail:
    """Soft-deactivate an agent — stops it from syncing but preserves the record."""
    import uuid
    agent = db.get(EvolutionAgent, uuid.UUID(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.active = False
    db.commit()
    db.refresh(agent)
    return _agent_detail(agent)


@router.delete("/agents/{agent_id}", status_code=204, response_model=None)
def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_staff),
) -> None:
    """Permanently delete an agent and its credentials."""
    import uuid
    agent = db.get(EvolutionAgent, uuid.UUID(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()