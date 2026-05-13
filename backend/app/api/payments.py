"""PayFast payment and subscription endpoints.

POST /api/payments/initiate              — create company + user, return PayFast form data
POST /api/payments/notify                — ITN webhook from PayFast (activates subscription)
GET  /api/payments/success               — redirect after successful payment
GET  /api/payments/cancel                — redirect after cancelled payment
GET  /api/payments/subscription          — get current subscription info (owner only)
POST /api/payments/subscription/change   — upgrade or downgrade plan with proration
POST /api/payments/subscription/cancel   — cancel subscription via PayFast API
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
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
    "starter": "Ghost CFO Starter R500/month",
    "professional": "Ghost CFO Professional R900/month",
    "premium": "Ghost CFO Premium R1500/month",
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
        param_string += "&passphrase=" + urllib.parse.quote_plus(
            settings.payfast_passphrase.strip()
        )
    return param_string


def _sign(data: dict[str, Any]) -> str:
    """Generate MD5 signature matching PayFast's PHP urlencode behavior."""
    param_string = _build_param_string(data)
    log.debug("payfast.signing param_string=%s", param_string)
    return hashlib.md5(param_string.encode()).hexdigest()


# ---------------------------------------------------------------------------
# PayFast Subscription API helpers
# ---------------------------------------------------------------------------


def _payfast_api_base() -> str:
    return (
        "https://api.sandbox.payfast.co.za"
        if settings.payfast_sandbox
        else "https://api.payfast.co.za"
    )


def _payfast_api_headers() -> dict[str, str]:
    """Generate authenticated headers for the PayFast REST API."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    params = {
        "merchant-id": settings.payfast_merchant_id,
        "passphrase": settings.payfast_passphrase,
        "timestamp": timestamp,
        "version": "v1",
    }
    parts = [
        f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted(params.items())
    ]
    signature = hashlib.md5("&".join(parts).encode()).hexdigest()
    return {
        "merchant-id": settings.payfast_merchant_id,
        "version": "v1",
        "timestamp": timestamp,
        "signature": signature,
    }


def _pf_fetch(token: str) -> dict | None:
    """Fetch subscription details from PayFast."""
    try:
        params = {"testing": "true"} if settings.payfast_sandbox else {}
        resp = httpx.get(
            f"{_payfast_api_base()}/subscriptions/{token}/fetch",
            headers=_payfast_api_headers(),
            params=params,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
        log.warning("pf.fetch status=%s body=%s", resp.status_code, resp.text[:300])
    except Exception as exc:
        log.warning("pf.fetch error: %s", exc)
    return None


def _pf_update(token: str, new_amount: int) -> bool:
    """Update the recurring amount on a PayFast subscription (amount in rands)."""
    try:
        params = {"testing": "true"} if settings.payfast_sandbox else {}
        resp = httpx.put(
            f"{_payfast_api_base()}/subscriptions/{token}/update",
            headers=_payfast_api_headers(),
            params=params,
            json={"amount": f"{new_amount:.2f}", "cycles": 0},
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        log.warning("pf.update status=%s body=%s", resp.status_code, resp.text[:300])
    except Exception as exc:
        log.warning("pf.update error: %s", exc)
    return False


def _pf_cancel(token: str) -> bool:
    """Cancel a PayFast subscription."""
    try:
        params = {"testing": "true"} if settings.payfast_sandbox else {}
        resp = httpx.put(
            f"{_payfast_api_base()}/subscriptions/{token}/cancel",
            headers=_payfast_api_headers(),
            params=params,
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        log.warning("pf.cancel status=%s body=%s", resp.status_code, resp.text[:300])
    except Exception as exc:
        log.warning("pf.cancel error: %s", exc)
    return False


def _pf_adhoc(token: str, amount: float, item_name: str, m_payment_id: str) -> bool:
    """Charge an ad-hoc amount against a PayFast subscription (amount in rands)."""
    try:
        params = {"testing": "true"} if settings.payfast_sandbox else {}
        resp = httpx.post(
            f"{_payfast_api_base()}/subscriptions/{token}/adhoc",
            headers=_payfast_api_headers(),
            params=params,
            json={
                "amount": f"{amount:.2f}",
                "item_name": item_name[:100],
                "m_payment_id": m_payment_id,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        log.warning("pf.adhoc status=%s body=%s", resp.status_code, resp.text[:300])
    except Exception as exc:
        log.warning("pf.adhoc error: %s", exc)
    return False


def _billing_cycle(plan_start_date: date) -> dict:
    """Calculate current billing cycle info from the plan start date."""
    today = date.today()
    days_elapsed = (today - plan_start_date).days
    completed_cycles = days_elapsed // 30
    days_into_cycle = days_elapsed % 30
    days_remaining = 30 - days_into_cycle
    next_billing_date = plan_start_date + timedelta(days=(completed_cycles + 1) * 30)
    return {
        "days_remaining": days_remaining,
        "days_into_cycle": days_into_cycle,
        "next_billing_date": next_billing_date,
    }


# ---------------------------------------------------------------------------
# Subscription management models
# ---------------------------------------------------------------------------


class SubscriptionInfo(BaseModel):
    plan: str
    plan_price: int
    subscription_status: str
    plan_start_date: date | None
    next_billing_date: date | None
    next_billing_amount: float | None
    days_remaining_in_cycle: int | None
    has_payfast_token: bool


class ChangePlanRequest(BaseModel):
    new_plan: str


class ChangePlanResponse(BaseModel):
    ok: bool
    message: str
    prorated_amount: float | None
    new_plan: str
    effective_date: str


# ---------------------------------------------------------------------------
# Subscription endpoints (owner only)
# ---------------------------------------------------------------------------

from app.api.deps import get_current_user  # noqa: E402


def _require_owner(user: Any) -> None:
    if user.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorised")


@router.get("/subscription", response_model=SubscriptionInfo)
def subscription_info(
    user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubscriptionInfo:
    """Return the current subscription details for the authenticated owner."""
    from app.models.company import Company

    _require_owner(user)
    if not user.company_id:
        raise HTTPException(
            status_code=404, detail="No company associated with this account"
        )

    company = db.get(Company, user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    billing = (
        _billing_cycle(company.plan_start_date) if company.plan_start_date else None
    )
    plan_price = PLAN_PRICES.get(company.plan, 0)

    return SubscriptionInfo(
        plan=company.plan,
        plan_price=plan_price,
        subscription_status=company.subscription_status,
        plan_start_date=company.plan_start_date,
        next_billing_date=billing["next_billing_date"] if billing else None,
        next_billing_amount=float(plan_price),
        days_remaining_in_cycle=billing["days_remaining"] if billing else None,
        has_payfast_token=bool(company.payfast_token),
    )


@router.post("/subscription/change", response_model=ChangePlanResponse)
def change_plan(
    body: ChangePlanRequest,
    user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangePlanResponse:
    """Upgrade or downgrade plan. Upgrades are prorated for remaining days."""
    from app.models.company import Company

    _require_owner(user)
    if body.new_plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {body.new_plan}")

    if not user.company_id:
        raise HTTPException(
            status_code=404, detail="No company associated with this account"
        )

    company = db.get(Company, user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if company.plan == body.new_plan:
        raise HTTPException(status_code=400, detail="Already on this plan")

    if not company.payfast_token:
        raise HTTPException(
            status_code=400,
            detail="No active PayFast subscription token found. Contact support.",
        )

    old_price = PLAN_PRICES[company.plan]
    new_price = PLAN_PRICES[body.new_plan]
    is_upgrade = new_price > old_price

    billing = (
        _billing_cycle(company.plan_start_date) if company.plan_start_date else None
    )
    days_remaining = billing["days_remaining"] if billing else 30
    next_billing_date = (
        billing["next_billing_date"] if billing else (date.today() + timedelta(days=30))
    )

    prorated_amount: float | None = None
    effective_date: str

    if is_upgrade:
        prorated_amount = round((new_price / 30) * days_remaining, 2)

        adhoc_ok = _pf_adhoc(
            token=company.payfast_token,
            amount=prorated_amount,
            item_name=f"Upgrade to {PLAN_NAMES[body.new_plan]} — {days_remaining} days",
            m_payment_id=str(company.id),
        )
        if not adhoc_ok:
            raise HTTPException(
                status_code=502,
                detail="PayFast could not process the prorated charge. Please try again.",
            )

        _pf_update(company.payfast_token, new_price)
        effective_date = date.today().isoformat()
        message = (
            f"Your plan has been upgraded to {body.new_plan.title()}. "
            f"A prorated charge of R{prorated_amount:.2f} was processed for the "
            f"remaining {days_remaining} days of your current billing cycle. "
            f"From {next_billing_date.isoformat()} you will be billed R{new_price}/month."
        )
    else:
        _pf_update(company.payfast_token, new_price)
        effective_date = next_billing_date.isoformat()
        message = (
            f"Your plan will be changed to {body.new_plan.title()} (R{new_price}/month) "
            f"at your next billing date on {next_billing_date.isoformat()}."
        )

    company.plan = body.new_plan
    db.commit()

    log.info(
        "subscription.change company=%s old=%s new=%s upgrade=%s prorated=%s",
        company.id,
        old_price,
        new_price,
        is_upgrade,
        prorated_amount,
    )

    return ChangePlanResponse(
        ok=True,
        message=message,
        prorated_amount=prorated_amount,
        new_plan=body.new_plan,
        effective_date=effective_date,
    )


@router.post("/subscription/cancel")
def cancel_subscription(
    user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel the PayFast subscription. Access remains until end of billing cycle."""
    from app.models.company import Company

    _require_owner(user)
    if not user.company_id:
        raise HTTPException(
            status_code=404, detail="No company associated with this account"
        )

    company = db.get(Company, user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if company.subscription_status == "cancelled":
        raise HTTPException(status_code=400, detail="Subscription is already cancelled")

    if not company.payfast_token:
        raise HTTPException(
            status_code=400,
            detail="No active PayFast subscription token found. Contact support.",
        )

    ok = _pf_cancel(company.payfast_token)
    if not ok:
        raise HTTPException(
            status_code=502,
            detail="PayFast could not process the cancellation. Please try again.",
        )

    company.subscription_status = "cancelled"
    db.commit()

    billing = (
        _billing_cycle(company.plan_start_date) if company.plan_start_date else None
    )
    access_until = (
        billing["next_billing_date"].isoformat() if billing else "end of current period"
    )

    log.info("subscription.cancel company=%s", company.id)
    return {
        "ok": True,
        "message": f"Your subscription has been cancelled. You will retain access until {access_until}.",
        "access_until": access_until,
    }


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
def initiate_payment(
    body: InitiateRequest, db: Session = Depends(get_db)
) -> InitiateResponse:
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

    # If a pending account already exists for this email, reuse it instead of creating duplicates
    existing = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()
    if existing:
        if existing.active:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please log in.",
            )
        # Pending user from a previous failed payment — reuse the company, update plan
        company = db.get(Company, existing.company_id)
        if company:
            company.plan = body.plan
            company.name = body.company_name
            company.owner_name = body.owner_name
            db.commit()
            db.refresh(company)
        else:
            db.delete(existing)
            db.flush()
            existing = None

    if not existing:
        # Fresh signup — create inactive company + user
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
        "cancel_url": f"{settings.base_url}/payments/cancel?pid={company.id}",
        "notify_url": f"{settings.base_url}/payments/notify",
        "name_first": body.owner_name.split()[0] if body.owner_name else "",
        "name_last": " ".join(body.owner_name.split()[1:])
        if body.owner_name and len(body.owner_name.split()) > 1
        else "",
        "email_address": body.email,
        "m_payment_id": m_payment_id,
        "amount": f"{amount:.2f}",
        "item_name": PLAN_NAMES[body.plan],
        "item_description": f"Monthly Ghost CFO subscription - {body.company_name}",
        "custom_str1": body.plan,
        "custom_str2": str(company.id),
        "subscription_type": "1",
        "billing_date": today,
        "recurring_amount": f"{amount:.2f}",
        "frequency": "3",
        "cycles": "0",
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
    body_str = body_bytes.decode()
    params = dict(urllib.parse.parse_qsl(body_str))

    log.info(
        "payment.itn received params=%s",
        {k: v for k, v in params.items() if "key" not in k.lower()},
    )

    # 1. Verify signature against the raw body — avoids re-encoding drift vs PayFast's PHP urlencode
    received_sig = params.get("signature", "")
    raw_parts = [seg for seg in body_str.split("&") if not seg.startswith("signature=")]
    raw_param_string = "&".join(raw_parts)
    if settings.payfast_passphrase:
        raw_param_string += "&passphrase=" + urllib.parse.quote_plus(
            settings.payfast_passphrase.strip()
        )
    expected_sig = hashlib.md5(raw_param_string.encode()).hexdigest()
    sig_ok = secrets.compare_digest(received_sig, expected_sig)
    if not sig_ok:
        log.warning(
            "payment.itn signature_mismatch received=%s expected=%s",
            received_sig,
            expected_sig,
        )

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
    resend.Emails.send(
        {
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [user.email],
            "subject": "Welcome to Ghost CFO — your account is active",
            "html": f"""
        <div style="font-family:Inter,sans-serif;max-width:520px;margin:auto;background:#000;color:#fff;padding:32px;border-radius:12px">
          <div style="margin-bottom:24px">
            <span style="font-size:22px;font-weight:700;background:linear-gradient(135deg,#2DD4BF,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent">Ghost CFO</span>
          </div>
          <h2 style="font-size:20px;margin:0 0 12px">Welcome, {company.owner_name or user.email}!</h2>
          <p style="color:#a1a1aa;line-height:1.6">Your Ghost CFO subscription is now active. Your first monthly financial report will be generated at month-end.</p>

          <div style="background:#111;border:1px solid #27272a;border-radius:8px;padding:16px;margin:20px 0">
            <p style="color:#71717a;font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.05em">Your login details</p>
            <p style="margin:4px 0;font-size:14px"><span style="color:#71717a">Email:</span> <strong style="color:#fff">{user.email}</strong></p>
            <p style="margin:4px 0;font-size:14px"><span style="color:#71717a">Password:</span> <span style="color:#a1a1aa">the password you chose during signup</span></p>
            <p style="margin:4px 0;font-size:14px"><span style="color:#71717a">Plan:</span> <span style="color:#2DD4BF">{company.plan.title()}</span></p>
          </div>

          <p style="color:#a1a1aa;line-height:1.6">Log in to complete your company profile and upload your first Pastel files:</p>
          <a href="{portal_url}" style="display:inline-block;margin:16px 0;padding:12px 28px;background:linear-gradient(135deg,#2DD4BF,#06B6D4);color:#000;font-weight:700;border-radius:8px;text-decoration:none">
            Open Portal
          </a>
          <p style="color:#52525b;font-size:12px;margin-top:32px">Powered by Numbers10 Technology Solutions &middot; numbers10.co.za</p>
        </div>
        """,
        }
    )


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
        "item_name": "Ghost CFO Starter R500/month",
        "item_description": "Monthly Ghost CFO subscription - Test Company",
        "custom_str1": "starter",
        "custom_str2": "00000000-0000-0000-0000-000000000001",
        "subscription_type": "1",
        "billing_date": date.today().isoformat(),
        "recurring_amount": "500.00",
        "frequency": "3",
        "cycles": "0",
    }
    param_no_passphrase = _build_param_string(test_fields, include_passphrase=False)
    param_with_passphrase = _build_param_string(test_fields, include_passphrase=True)
    return {
        "sandbox": settings.payfast_sandbox,
        "payfast_url": PAYFAST_URL,
        "merchant_id_set": bool(settings.payfast_merchant_id),
        "merchant_key_set": bool(settings.payfast_merchant_key),
        "passphrase_set": bool(settings.payfast_passphrase),
        "passphrase_length": len(settings.payfast_passphrase)
        if settings.payfast_passphrase
        else 0,
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
def payment_cancel(
    pid: str | None = None, db: Session = Depends(get_db)
) -> RedirectResponse:
    """Clean up pending company/user when buyer cancels on PayFast."""
    if pid:
        import uuid as _uuid
        from app.models.company import Company
        from app.models.user import User as UserModel
        from sqlalchemy import delete as sa_delete

        try:
            cid = _uuid.UUID(pid)
            company = db.get(Company, cid)
            if company and company.subscription_status == "pending":
                db.execute(sa_delete(UserModel).where(UserModel.company_id == cid))
                db.delete(company)
                db.commit()
                log.info("payment.cancel cleaned_up company=%s", cid)
        except Exception as exc:
            log.warning("payment.cancel cleanup_failed: %s", exc)
    return RedirectResponse(url="/signup?cancelled=true", status_code=302)
