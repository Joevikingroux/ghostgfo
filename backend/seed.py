"""Create the first admin user and optionally a test company.

Usage:
    python seed.py --password <choose-a-strong-password>
    python seed.py --email admin@numbers10.co.za --password <password>
    python seed.py --email admin@numbers10.co.za --password <password> --with-test-company
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import click
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.models.company import Company
from app.models.user import User

configure_logging()


@click.command()
@click.option("--email", default="admin@numbers10.co.za", show_default=True)
@click.option(
    "--password",
    default=None,
    help="Admin password. A random password is generated and printed if omitted.",
)
@click.option(
    "--with-test-company",
    is_flag=True,
    default=False,
    help="Also create ABC Hardware test company with placeholder credentials.",
)
def seed(email: str, password: str | None, with_test_company: bool) -> None:
    if not password:
        password = secrets.token_urlsafe(16)
        click.echo(f"  Generated admin password: {password}")
        click.echo("  (save this — it won't be shown again)")

    db = SessionLocal()
    try:
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing:
            click.echo(f"  Admin user {email} already exists — skipping.")
        else:
            admin = User(
                email=email,
                password_hash=hash_password(password),
                full_name="Numbers10 Admin",
                role="admin",
            )
            db.add(admin)
            db.commit()
            click.echo(f"  ✓ Admin user created: {email}")

        if with_test_company:
            company = db.execute(
                select(Company).where(Company.name == "ABC Hardware (Pty) Ltd")
            ).scalar_one_or_none()
            if not company:
                company = Company(
                    name="ABC Hardware (Pty) Ltd",
                    trading_name="ABC Hardware",
                    industry="Retail - Hardware",
                    owner_name="Test Owner",
                    owner_email="owner@example.co.za",
                    owner_telegram="",
                    bookkeeper_name="Test Bookkeeper",
                    bookkeeper_email="bookkeeper@example.co.za",
                    plan="professional",
                    data_source="partner",
                )
                db.add(company)
                db.commit()
                db.refresh(company)
                click.echo(f"  ✓ Test company created: {company.name} (id={company.id})")

                bk_pass = secrets.token_urlsafe(12)
                ow_pass = secrets.token_urlsafe(12)
                bookkeeper = User(
                    email="bookkeeper@example.co.za",
                    password_hash=hash_password(bk_pass),
                    full_name="Test Bookkeeper",
                    role="bookkeeper",
                    company_id=company.id,
                )
                owner = User(
                    email="owner@example.co.za",
                    password_hash=hash_password(ow_pass),
                    full_name="Test Owner",
                    role="owner",
                    company_id=company.id,
                )
                db.add_all([bookkeeper, owner])
                db.commit()
                click.echo(f"  ✓ Test bookkeeper: bookkeeper@example.co.za / {bk_pass}")
                click.echo(f"  ✓ Test owner:      owner@example.co.za / {ow_pass}")
            else:
                click.echo("  Test company already exists — skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
