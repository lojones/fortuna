import logging
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserCreate, UserInDB, UserPublic
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


def _user_from_doc(doc: dict) -> UserInDB:
    return UserInDB(
        id=str(doc["_id"]),
        username=doc["username"],
        email=doc["email"],
        role=doc["role"],
        status=doc["status"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        approved_by=str(doc["approved_by"]) if doc.get("approved_by") else None,
        approved_at=doc.get("approved_at"),
    )


def _user_to_public(user: UserInDB) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
    )


async def create_user(db: AsyncIOMotorDatabase, user_create: UserCreate) -> UserInDB:
    logger.debug(f"Creating user: username='{user_create.username}', email='{user_create.email}'")

    # Check username uniqueness
    existing = await db.users.find_one({"username": user_create.username})
    if existing:
        logger.info(f"Registration rejected: username='{user_create.username}' already taken")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Check email uniqueness
    existing = await db.users.find_one({"email": user_create.email})
    if existing:
        logger.info(f"Registration rejected: email='{user_create.email}' already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    now = datetime.now(timezone.utc)
    hashed = hash_password(user_create.password)

    doc = {
        "username": user_create.username,
        "email": user_create.email,
        "hashed_password": hashed,
        "role": "user",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "approved_by": None,
        "approved_at": None,
    }

    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info(f"User created: id={result.inserted_id}, username='{user_create.username}', status=pending")
    return _user_from_doc(doc)


async def get_user_by_username(
    db: AsyncIOMotorDatabase, username: str
) -> Optional[UserInDB]:
    doc = await db.users.find_one({"username": username})
    if doc:
        return _user_from_doc(doc)
    return None


async def get_user_by_id(
    db: AsyncIOMotorDatabase, user_id: str
) -> Optional[UserInDB]:
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if doc:
        return _user_from_doc(doc)
    return None


async def get_all_users(db: AsyncIOMotorDatabase) -> List[UserInDB]:
    users = []
    async for doc in db.users.find():
        users.append(_user_from_doc(doc))
    return users


async def get_pending_users(db: AsyncIOMotorDatabase) -> List[UserInDB]:
    users = []
    async for doc in db.users.find({"status": "pending"}):
        users.append(_user_from_doc(doc))
    return users


async def update_user_status(
    db: AsyncIOMotorDatabase,
    user_id: str,
    new_status: str,
    approved_by_id: Optional[str] = None,
) -> UserInDB:
    logger.info(f"Updating status for user_id={user_id} to '{new_status}'" +
                (f" (approved_by={approved_by_id})" if approved_by_id else ""))
    now = datetime.now(timezone.utc)
    update = {"$set": {"status": new_status, "updated_at": now}}

    if new_status == "active" and approved_by_id:
        update["$set"]["approved_by"] = ObjectId(approved_by_id)
        update["$set"]["approved_at"] = now

    result = await db.users.find_one_and_update(
        {"_id": ObjectId(user_id)}, update, return_document=True
    )
    if not result:
        logger.warning(f"update_user_status: user_id={user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    logger.info(f"User id={user_id} status updated to '{new_status}'")
    return _user_from_doc(result)


async def update_user_role(
    db: AsyncIOMotorDatabase, user_id: str, role: str
) -> UserInDB:
    logger.info(f"Updating role for user_id={user_id} to '{role}'")
    now = datetime.now(timezone.utc)
    result = await db.users.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role, "updated_at": now}},
        return_document=True,
    )
    if not result:
        logger.warning(f"update_user_role: user_id={user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    logger.info(f"User id={user_id} role updated to '{role}'")
    return _user_from_doc(result)


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> None:
    logger.info(f"Attempting to delete user_id={user_id}")
    # Check if user is the last admin
    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"delete_user: user_id={user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.role == "admin":
        admin_count = await db.users.count_documents({"role": "admin"})
        logger.debug(f"delete_user: target is admin, current admin count={admin_count}")
        if admin_count <= 1:
            logger.warning(f"delete_user: refusing to delete last admin (user_id={user_id})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only admin user",
            )

    await db.users.delete_one({"_id": ObjectId(user_id)})
    logger.info(f"User id={user_id} ('{user.username}') deleted")
