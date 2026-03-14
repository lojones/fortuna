"""
Admin password reset utility.

bcrypt passwords stored in the database are one-way hashes and CANNOT be
decrypted.  Use this script to reset an admin (or any user's) password by
hashing a new plaintext password and writing it directly to MongoDB.

Usage
-----
    # Interactive (prompts for new password, hidden input)
    python reset_admin_password.py

    # Non-interactive (pass username via --username flag)
    python reset_admin_password.py --username admin

    # Fully non-interactive (pass new password via --password flag)
    python reset_admin_password.py --username admin --password newSecret123
"""

import argparse
import asyncio
import getpass
import logging
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Allow the script to be run from the backend/ directory without installing
# the package, while still importing app modules the same way the app does.
# ---------------------------------------------------------------------------
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.mongodb import get_client, get_database
from app.services.auth_service import hash_password

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8


async def reset_password(username: str, new_password: str) -> None:
    db = get_database()

    user_doc = await db.users.find_one({"username": username})
    if user_doc is None:
        logger.error(f"No user found with username '{username}'.")
        sys.exit(1)

    hashed = hash_password(new_password)
    result = await db.users.update_one(
        {"username": username},
        {"$set": {"hashed_password": hashed, "updated_at": datetime.now(timezone.utc)}},
    )

    if result.modified_count == 1:
        logger.info(f"Password for user '{username}' has been reset successfully.")
    else:
        logger.error("Database update did not modify any document. Password was NOT changed.")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset a Fortuna user password directly in MongoDB."
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Username whose password should be reset (default: prompted interactively).",
    )
    parser.add_argument(
        "--password",
        default=None,
        help=(
            "New plaintext password (default: prompted interactively with hidden input). "
            "Avoid using this flag in shared environments — prefer the interactive prompt."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    username: str = args.username or input("Username to reset: ").strip()
    if not username:
        logger.error("Username cannot be empty.")
        sys.exit(1)

    if args.password:
        new_password = args.password
    else:
        new_password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm new password: ")
        if new_password != confirm:
            logger.error("Passwords do not match. Aborting.")
            sys.exit(1)

    if len(new_password) < MIN_PASSWORD_LENGTH:
        logger.error(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long. Aborting."
        )
        sys.exit(1)

    try:
        asyncio.run(reset_password(username, new_password))
    finally:
        # Close the Motor client so the event loop exits cleanly.
        get_client().close()


if __name__ == "__main__":
    main()
