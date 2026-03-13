import logging

from fastapi import APIRouter, HTTPException, status

from app.db.mongodb import get_database
from app.models.user import LoginRequest, LoginResponse, UserCreate, UserPublic, RegisterResponse
from app.services.auth_service import verify_password, create_access_token
from app.services import user_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    logger.info(f"Login attempt for username='{body.username}'")
    db = get_database()
    user = await user_service.get_user_by_username(db, body.username)
    if not user or not verify_password(
        body.password,
        (await db.users.find_one({"username": body.username}))["hashed_password"],
    ):
        logger.warning(f"Failed login attempt for username='{body.username}': invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.status == "pending":
        logger.info(f"Login denied for username='{body.username}': account pending approval")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending admin approval",
        )

    if user.status == "suspended":
        logger.warning(f"Login denied for username='{body.username}': account suspended")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role}
    )
    logger.info(f"Login successful for username='{body.username}' (id={user.id}, role={user.role})")

    return LoginResponse(
        access_token=token,
        user=UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
        ),
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    logger.info(f"Registration attempt for username='{body.username}', email='{body.email}'")
    db = get_database()
    user = await user_service.create_user(db, body)
    logger.info(f"Registration successful for username='{body.username}' (id={user.id}), status=pending")

    return RegisterResponse(
        message="Registration successful. Awaiting admin approval.",
        user=UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
        ),
    )
