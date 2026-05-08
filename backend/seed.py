"""Create the first admin user and optionally a test company.

Usage:
    python seed.py
    python seed.py --email admin@numbers10.co.za --password secret123
    python seed.py --email admin@numbers10.co.za --password secret123 --with-test-company
"""
from __future__ import annotations

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
@click.option("--password", default="changeme123", show_default=True)
@click.option(
    "--with-test-company",
    is_flag=True,
    default=False,
    help="Also create ABC Hardware test company.",
)
def seed(email: str, password: str, with_test_company: bool) -> None:
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
                    owner_name="Johan van Rensburg",
                    owner_email="johan@abchardware.co.za",
                    owner_whatsapp="+27821234567",
                    bookkeeper_name="Sandra Botha",
                    bookkeeper_email="sandra@abchardware.co.za",
                    plan="professional",
                    data_source="partner",
                )
                db.add(company)
                db.commit()
                db.refresh(company)
                click.echo(f"  ✓ Test company created: {company.name} (id={company.id})")

                bookkeeper = User(
                    email="sandra@abchardware.co.za",
                    password_hash=hash_password("testpass123"),
                    full_name="Sandra Botha",
                    role="bookkeeper",
                    company_id=company.id,
                )
                owner = User(
                    email="johan@abchardware.co.za",
                    password_hash=hash_password("testpass123"),
                    full_name="Johan van Rensburg",
                    role="owner",
                    company_id=company.id,
                )
                db.add_all([bookkeeper, owner])
                db.commit()
                click.echo("  ✓ Test company users created (bookkeeper + owner)")
            else:
                click.echo("  Test company already exists — skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
