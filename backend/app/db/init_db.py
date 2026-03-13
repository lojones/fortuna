import logging
from datetime import datetime, timezone

from app.config import settings
from app.db.mongodb import get_database
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


async def init_db():
    """Seed default admin user if no admins exist."""
    db = get_database()

    # Create indexes
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("status")
    await db.visualizations.create_index("owner_id")
    await db.visualizations.create_index("status")
    await db.visualizations.create_index([("owner_id", 1), ("status", 1)])
    await db.visualizations.create_index("published_slug", unique=True, sparse=True)
    await db.chat_sessions.create_index("visualization_id")
    await db.chat_sessions.create_index("owner_id")

    admin_count = await db.users.count_documents({"role": "admin"})
    if admin_count == 0:
        now = datetime.now(timezone.utc)
        hashed = hash_password(settings.DEFAULT_ADMIN_PASSWORD)
        await db.users.insert_one({
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "email": settings.DEFAULT_ADMIN_EMAIL,
            "hashed_password": hashed,
            "role": "admin",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "approved_by": None,
            "approved_at": None,
        })
        logger.info("Default admin user created")
    else:
        logger.info("Admin user already exists, skipping seed")
