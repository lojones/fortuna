import logging
from typing import List

from fastapi import APIRouter, Depends

from app.db.mongodb import get_database
from app.models.user import UserPublic, UserInDB, RoleUpdate
from app.services.auth_service import get_current_user, require_admin
from app.services import user_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_public(user: UserInDB) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    logger.debug(f"GET /me for user='{current_user.username}' (id={current_user.id})")
    return _to_public(current_user)


@router.get("", response_model=List[UserPublic])
async def get_all_users(admin: UserInDB = Depends(require_admin)):
    logger.info(f"Admin '{admin.username}' fetching all users")
    db = get_database()
    users = await user_service.get_all_users(db)
    logger.debug(f"Returning {len(users)} users")
    return [_to_public(u) for u in users]


@router.get("/pending", response_model=List[UserPublic])
async def get_pending_users(admin: UserInDB = Depends(require_admin)):
    logger.debug(f"Admin '{admin.username}' fetching pending users")
    db = get_database()
    users = await user_service.get_pending_users(db)
    logger.info(f"Found {len(users)} pending user(s)")
    return [_to_public(u) for u in users]


@router.patch("/{user_id}/approve", response_model=UserPublic)
async def approve_user(user_id: str, admin: UserInDB = Depends(require_admin)):
    logger.info(f"Admin '{admin.username}' approving user id={user_id}")
    db = get_database()
    user = await user_service.update_user_status(db, user_id, "active", admin.id)
    logger.info(f"User id={user_id} ('{user.username}') approved by admin '{admin.username}'")
    return _to_public(user)


@router.patch("/{user_id}/suspend", response_model=UserPublic)
async def suspend_user(user_id: str, admin: UserInDB = Depends(require_admin)):
    logger.info(f"Admin '{admin.username}' suspending user id={user_id}")
    db = get_database()
    user = await user_service.update_user_status(db, user_id, "suspended")
    logger.info(f"User id={user_id} ('{user.username}') suspended by admin '{admin.username}'")
    return _to_public(user)


@router.patch("/{user_id}/role", response_model=UserPublic)
async def update_role(
    user_id: str, body: RoleUpdate, admin: UserInDB = Depends(require_admin)
):
    logger.info(f"Admin '{admin.username}' changing role of user id={user_id} to '{body.role}'")
    db = get_database()
    user = await user_service.update_user_role(db, user_id, body.role)
    logger.info(f"User id={user_id} ('{user.username}') role updated to '{body.role}'")
    return _to_public(user)


@router.delete("/{user_id}")
async def delete_user(user_id: str, admin: UserInDB = Depends(require_admin)):
    logger.info(f"Admin '{admin.username}' deleting user id={user_id}")
    db = get_database()
    await user_service.delete_user(db, user_id)
    logger.info(f"User id={user_id} deleted by admin '{admin.username}'")
    return {"message": "User deleted"}
