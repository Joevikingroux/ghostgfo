"""PayFast payment and subscription endpoints.

POST /api/payments/initiate   — create company + user, return PayFast form data
POST /api/payments/notify     — ITN webhook from PayFast (activates subscription)
GET  /api/payments/success    — redirect after successful payment
GET  /api/payments/cancel     — redirect after cancelled payment
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import urllib.parse
from datetime import date, datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

log = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

PLAN_PRICES = {
    "starter": 500,
    "professional": 900,
    "premium": 1500,
}

PLAN_NAMES = {
    "starter": "Ghost CFO Starter — R500/month",
    "professional": "Ghost CFO Professional — R900/month",
    "premium": "Ghost CFO Premium — R1,500/month",
}

PAYFAST_URL = (
    "https://sandbox.payfast.co.za/eng/process"
    if settings.payfast_sandbox
    else "https://www.payfast.co.za/eng/process"
)


# ---------------------------------------------------------------------------
# Signature helper
# ---------------------------------------------------------------------------

def _build_param_string(data: dict[str, Any], include_passphrase: bool = True) -> str:
    """Build the raw param string PayFast expects (before MD5)."""
    parts = []
    for k, v in data.items():
        if k == "signature":
            continue
        val = str(v).strip()
        if val == "":
            continue
        parts.append(f"{k}={urllib.parse.quote_plus(val)}")
    param_string = "&".join(parts)
    if include_passphrase and settings.payfast_passphrase:
        param_string += "&passphrase=" + urllib.parse.quote_plus(settings.payfast_passphrase.strip())
    return param_string


def _sign(data: dict[str, Any]) -> str:
    """Generate MD5 signature matching PayFast's PHP urlencode behavior."""
    param_string = _build_param_string(data)
    log.debug("payfast.signing param_string=%s", param_string)
    return hashlib.md5(param_string.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Initiate: create account + return PayFast fields
# ---------------------------------------------------------------------------

class InitiateRequest(BaseModel):
    plan: str
    company_name: str
    owner_name: str
    email: EmailStr
    password: str


class InitiateResponse(BaseModel):
    payfast_url: str
    fields: dict[str, str]


@router.post("/initiate", response_model=InitiateResponse)
def initiate_payment(body: InitiateRequest, db: Session = Depends(get_db)) -> InitiateResponse:
    """Create a pending company + user account then return PayFast form fields."""
    from app.core.security import hash_password
    from app.models.company import Company
    from app.models.user import User
    from sqlalchemy import select

    if body.plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {body.plan}")

    if not settings.payfast_merchant_id:
        raise HTTPException(
            status_code=503,
            detail="PayFast is not configured yet. Contact Numbers10 to activate your account.",
        )

    # Check email not already registered
    existing = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please log in.")

    # Create inactive company + user
    company = Company(
        name=body.company_name,
        owner_name=body.owner_name,
        owner_email=body.email,
        plan=body.plan,
        active=False,
        subscription_status="pending",
    )
    db.add(company)
    db.flush()

    user = User(
        company_id=company.id,
        email=body.email,
        full_name=body.owner_name,
        password_hash=hash_password(body.password),
        role="owner",
        active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(company)

    amount = PLAN_PRICES[body.plan]
    m_payment_id = str(company.id)
    today = date.today().isoformat()

    fields: dict[str, str] = {
        "merchant_id": settings.payfast_merchant_id,
        "merchant_key": settings.payfast_merchant_key,
        "return_url": f"{settings.base_url}/payments/success",
        "cancel_url": f"{settings.base_url}/payments/cancel",
        "notify_url": f"{settings.base_url}/payments/notify",
        "name_first": body.owner_name.split()[0] if body.owner_name else "",
        "name_last": " ".join(body.owner_name.split()[1:]) if body.owner_name and len(body.owner_name.split()) > 1 else "",
        "email_address": body.email,
        "m_payment_id": m_payment_id,
        "amount": f"{amount:.2f}",
        "item_name": PLAN_NAMES[body.plan],
        "item_description": f"Monthly Ghost CFO subscription — {body.company_name}",
        "subscription_type": "1",
        "billing_date": today,
        "recurring_amount": f"{amount:.2f}",
        "frequency": "3",    # monthly
        "cycles": "0",       # indefinite
        "custom_str1": body.plan,
        "custom_str2": str(company.id),
    }
    fields["signature"] = _sign(fields)

    log.info("payment.initiate company=%s plan=%s", company.id, body.plan)
    return InitiateResponse(payfast_url=PAYFAST_URL, fields=fields)


# ---------------------------------------------------------------------------
# ITN webhook — PayFast POSTs here after successful payment
# ---------------------------------------------------------------------------

@router.post("/notify", status_code=200)
async def payfast_notify(request: Request, db: Session = Depends(get_db)) -> str:
    """Instant Transaction Notification from PayFast — activates the subscription."""
    from app.models.company import Company
    from app.models.user import User
    from sqlalchemy import select

    body_bytes = await request.body()
    params = dict(urllib.parse.parse_qsl(body_bytes.decode()))

    log.info("payment.itn received params=%s", {k: v for k, v in params.items() if "key" not in k.lower()})

    # 1. Verify signature
    received_sig = params.pop("signature", "")
    expected_sig = _sign(params)
    if not secrets.compare_digest(received_sig, expected_sig):
        log.warning("payment.itn signature_mismatch")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Verify payment status
    if params.get("payment_status") != "COMPLETE":
        log.info("payment.itn status=%s — ignoring", params.get("payment_status"))
        return "ok"

    # 3. Look up company
    company_id = params.get("custom_str2") or params.get("m_payment_id")
    if not company_id:
        log.warning("payment.itn no company_id in params")
        return "ok"

    import uuid as _uuid
    try:
        cid = _uuid.UUID(company_id)
    except ValueError:
        log.warning("payment.itn invalid company_id=%s", company_id)
        return "ok"

    company = db.get(Company, cid)
    if not company:
        log.warning("payment.itn company_not_found id=%s", cid)
        return "ok"

    # 4. Activate
    plan = params.get("custom_str1") or company.plan
    token = params.get("token", "")

    company.active = True
    company.plan = plan
    company.subscription_status = "active"
    company.payfast_token = token
    company.plan_start_date = date.today()

    # Activate the owner user
    user = db.execute(
        select(User).where(User.company_id == cid, User.role == "owner")
    ).scalar_one_or_none()
    if user:
        user.active = True

    db.commit()
    log.info("payment.itn activated company=%s plan=%s token=%s", cid, plan, token)

    # Send welcome email (best-effort)
    try:
        _send_welcome_email(company, user)
    except Exception as exc:
        log.warning("payment.itn welcome_email_failed: %s", exc)

    return "ok"


def _send_welcome_email(company: Any, user: Any) -> None:
    """Send a welcome email after subscription activation."""
    import resend
    resend.api_key = settings.resend_api_key
    if not settings.resend_api_key or not (user and user.email):
        return

    portal_url = settings.base_url + "/login"
    resend.Emails.send({
        "from": f"{settings.from_name} <{settings.from_email}>",
        "to": [user.email],
        "subject": f"Welcome to Ghost CFO — your account is active",
        "html": f"""
        <div style="font-family:Inter,sans-serif;max-width:520px;margin:auto;background:#000;color:#fff;padding:32px;border-radius:12px">
          <div style="margin-bottom:24px">
            <span style="font-size:22px;font-weight:700;background:linear-gradient(135deg,#2DD4BF,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent">Ghost CFO</span>
          </div>
          <h2 style="font-size:20px;margin:0 0 12px">Welcome, {company.owner_name or user.email}!</h2>
          <p style="color:#a1a1aa;line-height:1.6">Your Ghost CFO subscription is now active. Your first monthly financial report will be generated at month-end.</p>
          <p style="color:#a1a1aa;line-height:1.6">Log in to your portal to upload your Pastel files or check your report status:</p>
          <a href="{portal_url}" style="display:inline-block;margin:16px 0;padding:12px 28px;background:linear-gradient(135deg,#2DD4BF,#06B6D4);color:#000;font-weight:700;border-radius:8px;text-decoration:none">
            Open Portal
          </a>
          <p style="color:#52525b;font-size:12px;margin-top:32px">Powered by Numbers10 Technology Solutions · numbers10.co.za</p>
        </div>
        """,
    })


# ---------------------------------------------------------------------------
# Success / cancel redirects (these are browser redirects from PayFast)
# ---------------------------------------------------------------------------

@router.get("/config-test")
def config_test() -> dict:
    """Admin debug: verify PayFast config and expose test param string for signature comparison."""
    test_fields: dict[str, str] = {
        "merchant_id": settings.payfast_merchant_id or "NOT_SET",
        "merchant_key": settings.payfast_merchant_key or "NOT_SET",
        "return_url": f"{settings.base_url}/payments/success",
        "cancel_url": f"{settings.base_url}/payments/cancel",
        "notify_url": f"{settings.base_url}/payments/notify",
        "name_first": "Test",
        "name_last": "User",
        "email_address": "test@ghostcfo.co.za",
        "m_payment_id": "00000000-0000-0000-0000-000000000001",
        "amount": "500.00",
        "item_name": "Ghost CFO Starter — R500/month",
        "item_description": "Monthly Ghost CFO subscription — Test Company",
        "subscription_type": "1",
        "billing_date": date.today().isoformat(),
        "recurring_amount": "500.00",
        "frequency": "3",
        "cycles": "0",
        "custom_str1": "starter",
        "custom_str2": "00000000-0000-0000-0000-000000000001",
    }
    param_no_passphrase = _build_param_string(test_fields, include_passphrase=False)
    param_with_passphrase = _build_param_string(test_fields, include_passphrase=True)
    return {
        "sandbox": settings.payfast_sandbox,
        "payfast_url": PAYFAST_URL,
        "merchant_id_set": bool(settings.payfast_merchant_id),
        "merchant_key_set": bool(settings.payfast_merchant_key),
        "passphrase_set": bool(settings.payfast_passphrase),
        "passphrase_length": len(settings.payfast_passphrase) if settings.payfast_passphrase else 0,
        "param_string_without_passphrase": param_no_passphrase,
        "param_string_with_passphrase": param_with_passphrase,
        "md5_signature": hashlib.md5(param_with_passphrase.encode()).hexdigest(),
        "instructions": (
            "Paste 'param_string_without_passphrase' into https://sandbox.payfast.co.za/tools/signature_tester "
            "with your passphrase and verify the MD5 matches 'md5_signature'."
        ),
    }


@router.get("/success")
def payment_success() -> RedirectResponse:
    return RedirectResponse(url="/login?payment=success", status_code=302)


@router.get("/cancel")
def payment_cancel() -> RedirectResponse:
    return RedirectResponse(url="/?payment=cancelled", status_code=302)
