import argparse
import hashlib
import secrets
from datetime import datetime, timedelta

from backend.db import BetaToken, SessionLocal, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a beta access token.")
    parser.add_argument("--minutes", type=int, default=3, help="Total media minutes allowed.")
    parser.add_argument("--expires-days", type=int, default=7, help="Days before the token expires.")
    args = parser.parse_args()

    if args.minutes <= 0 or args.expires_days <= 0:
        parser.error("minutes and expires-days must be positive")

    init_db()
    token = secrets.token_urlsafe(12)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    db = SessionLocal()
    try:
        db.add(
            BetaToken(
                token_hash=token_hash,
                allowed_seconds=args.minutes * 60,
                expires_at=datetime.utcnow() + timedelta(days=args.expires_days),
            )
        )
        db.commit()
    finally:
        db.close()

    print(token)


if __name__ == "__main__":
    main()