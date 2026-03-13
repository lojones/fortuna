import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.db.mongodb import get_database
from app.models.user import UserInDB

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer()


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        logger.debug(f"Token decoded successfully for sub='{payload.get('sub')}'")
        return payload
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInDB:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("get_current_user: token missing 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    from bson import ObjectId

    db = get_database()
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        logger.warning(f"get_current_user: user_id={user_id} not found in DB")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    user = _user_from_doc(doc)
    logger.debug(f"Authenticated user='{user.username}' (id={user.id}, role={user.role}, status={user.status})")

    if user.status != "active":
        logger.warning(f"Access denied for user='{user.username}': status='{user.status}'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active",
        )

    return user


async def require_admin(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if current_user.role != "admin":
        logger.warning(f"Admin access denied for user='{current_user.username}' (role={current_user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    logger.debug(f"Admin access granted to user='{current_user.username}'")
    return current_user
