"""
Emergency admin password reset — run directly on the server when locked out.

Usage (via docker exec — most common):
    docker exec -it ghostcfo-api-1 python reset_admin_password.py joe@numbers10.co.za

What it does:
  - Sets a new password you type at the prompt
  - Clears must_change_password flag
  - Does NOT touch 2FA — combine with reset_2fa.py if also locked out of 2FA

Security: requires SSH / physical access to the server — no API endpoint.
"""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python reset_admin_password.py <email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()

    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models.user import User
    from sqlalchemy import select
    import getpass

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            print(f"ERROR: No user found with email '{email}'")
            sys.exit(1)

        print("\nUser found:")
        print(f"  Email : {user.email}")
        print(f"  Name  : {user.full_name or '(none)'}")
        print(f"  Role  : {user.role}")
        print(f"  2FA   : {'ENABLED' if user.totp_enabled else 'disabled'}")

        new_password = getpass.getpass("\nNew password (hidden): ").strip()
        if len(new_password) < 8:
            print("ERROR: Password must be at least 8 characters.")
            sys.exit(1)

        confirm = getpass.getpass("Confirm new password: ").strip()
        if new_password != confirm:
            print("ERROR: Passwords do not match.")
            sys.exit(1)

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        db.commit()

        print(f"\n✓ Password updated for {user.email}.")
        if user.totp_enabled:
            print("  Note: 2FA is still enabled. If you also need to reset 2FA, run:")
            print(f"  docker exec -it ghostcfo-api-1 python reset_2fa.py {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
