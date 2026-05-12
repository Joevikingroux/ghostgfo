"""
Emergency 2FA reset — run directly on the server when an admin is locked out.

Usage (from /opt/ghostcfo/backend, or via docker exec):
    python reset_2fa.py joe@numbers10.co.za

Via docker exec (most common):
    docker exec -it ghostcfo-api-1 python reset_2fa.py joe@numbers10.co.za

What it does:
  - Clears totp_secret and totp_enrolled_at
  - Sets totp_enabled = False
  - Does NOT change the password or any other field
  - Prints confirmation before making any change

Security: requires SSH / physical access to the server — no API endpoint,
no way to trigger this remotely.
"""
from __future__ import annotations

import sys

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python reset_2fa.py <email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()

    from app.core.database import SessionLocal
    from app.models.user import User
    from sqlalchemy import select

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            print(f"ERROR: No user found with email '{email}'")
            sys.exit(1)

        print(f"\nUser found:")
        print(f"  Email : {user.email}")
        print(f"  Name  : {user.full_name or '(none)'}")
        print(f"  Role  : {user.role}")
        print(f"  2FA   : {'ENABLED' if user.totp_enabled else 'already disabled'}")

        if not user.totp_enabled:
            print("\n2FA is not enabled for this user — nothing to reset.")
            return

        confirm = input("\nReset 2FA for this user? Type YES to confirm: ").strip()
        if confirm != "YES":
            print("Aborted.")
            return

        user.totp_secret = None
        user.totp_enabled = False
        user.totp_enrolled_at = None
        db.commit()

        print(f"\n✓ 2FA has been cleared for {user.email}.")
        print("  The user can now log in with their password only and re-enrol 2FA from Settings.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
