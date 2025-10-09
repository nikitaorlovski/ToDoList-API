import asyncio
import time
from typing import Dict, Tuple

from fastapi import APIRouter, Depends, Form, Header, HTTPException, status
from jwt.exceptions import InvalidTokenError
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from core.config import settings
from core.security import decode_jwt, encode_jwt, hash_password, validate_password
from db.database import get_session
from db.models.user import UserOrm
from db.schemas.token import Token
from db.schemas.user import UserCreate
from repositories.user_repository import UserRepository

router = APIRouter(tags=["Authentication"], prefix="/api")
TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
RATE_LIMIT = 15
WINDOW_SIZE = 60
requests_count = {}
_requests_count: Dict[str, Tuple[int, int]] = {}
_lock = asyncio.Lock()


async def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def base_url(request: Request) -> str:  # pragma: no cover
    return str(request.base_url).rstrip("/")


def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get("access_token")


def auth_header(token: str | None) -> dict:
    return {"Authorization": token} if token else {}


@router.post("/registration", response_model=Token)
async def registration(
    user: UserCreate, repo: UserRepository = Depends(get_user_repo)
) -> Token:
    if await repo.get_by_email(user.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email уже зарегистрирован."
        )

    hashed_password = hash_password(user.password)
    db_user = UserOrm(email=user.email, name=user.name, hashed_password=hashed_password)
    await repo.add_user(db_user)
    access_token = await create_access_token(db_user)
    refresh_token = await create_refresh_token(db_user)
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="Bearer"
    )


async def validate_current_user(
    email: EmailStr = Form(...),
    password: str = Form(...),
    repo: UserRepository = Depends(get_user_repo),
) -> UserOrm:
    unauth_exc = HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail="Некорректный юзернейм или пароль"
    )
    if not (user := await repo.get_by_email(email)):
        raise unauth_exc
    if validate_password(user.hashed_password, password):
        return user
    else:
        raise unauth_exc


async def get_current_token_payload(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict:

    raw = None

    if authorization and authorization.lower().startswith("bearer "):
        raw = authorization.split(" ", 1)[1]

    if raw is None:
        cookie_val = request.cookies.get("access_token")
        if cookie_val:
            raw = cookie_val.split(" ", 1)[1] if " " in cookie_val else cookie_val

    if not raw:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Отсутствует токен")

    try:
        payload = decode_jwt(raw)
    except InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token error")
    return payload


async def create_jwt(
    token_type: str,
    token_data: dict,
    expire_minutes: int,
) -> str:
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(token_data)
    return encode_jwt(payload=jwt_payload, expire_minutes=expire_minutes)


async def create_access_token(user: UserOrm) -> str:
    return await create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data={"sub": str(user.email)},
        expire_minutes=settings.auth_jwt.access_token_expire,
    )


async def create_refresh_token(user: UserOrm):
    return await create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data={"sub": str(user.email)},
        expire_minutes=settings.auth_jwt.refresh_token_expire_days * 24 * 60,
    )


async def validate_token_type(payload: dict, token_type: str):
    token_type_payload = payload.get(TOKEN_TYPE_FIELD)
    if token_type_payload != token_type:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=f"Неправильный тип токена: {token_type_payload!r} когда ожидался {token_type!r}",
        )


async def get_user_from_sub(payload: dict, repo: UserRepository):
    email: str | None = payload.get("sub")
    unauth_exc = HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден"
    )
    if not (user := await repo.get_by_email(email)):
        raise unauth_exc
    return user


def get_auth_user_from_token_of_type(token_type: str):
    async def get_auth_user_from_token(
        payload: dict = Depends(get_current_token_payload),
        repo: UserRepository = Depends(get_user_repo),
    ) -> UserOrm:
        await validate_token_type(payload, token_type)
        return await get_user_from_sub(payload, repo)

    return get_auth_user_from_token


get_current_auth_user_for_refresh = get_auth_user_from_token_of_type(REFRESH_TOKEN_TYPE)
get_current_auth_user = get_auth_user_from_token_of_type(ACCESS_TOKEN_TYPE)


async def rate_limiter(
    user: UserOrm = Depends(get_current_auth_user),
):  # pragma: no cover

    now = int(time.time())
    window_start = now - (now % WINDOW_SIZE)
    key = f"user:{user.id}"

    async with _lock:
        count, start = _requests_count.get(key, (0, window_start))

        if start != window_start:
            count = 0
            start = window_start

        if count >= RATE_LIMIT:

            raise HTTPException(status_code=429, detail="Слишком много запросов")

        _requests_count[key] = (count + 1, start)


@router.post("/login", response_model=Token)
async def login(user: UserOrm = Depends(validate_current_user)):
    access_token = await create_access_token(user=user)
    refresh_token = await create_refresh_token(user=user)
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="Bearer"
    )
