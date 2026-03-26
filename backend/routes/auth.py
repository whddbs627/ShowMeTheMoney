from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.auth import hash_password, verify_password, create_token, encrypt_key, decrypt_key
from backend.database import (
    create_user, get_user_by_username, update_user_keys,
    update_user_discord, update_user_strategy,
)
from backend.auth import get_current_user
from fastapi import Depends

router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ApiKeysRequest(BaseModel):
    access_key: str
    secret_key: str


class DiscordRequest(BaseModel):
    webhook_url: str


class StrategyRequest(BaseModel):
    k: float = 0.5
    use_ma: bool = True
    use_rsi: bool = True
    rsi_lower: float = 30.0
    loss_pct: float = 0.03
    max_investment_krw: float = 100000


@router.post("/auth/register")
async def register(req: RegisterRequest):
    if len(req.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    existing = await get_user_by_username(req.username)
    if existing:
        raise HTTPException(400, "Username already taken")

    user_id = await create_user(req.username, hash_password(req.password))
    token = create_token(user_id)
    return {"token": token, "user_id": user_id, "username": req.username}


@router.post("/auth/login")
async def login(req: LoginRequest):
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")

    token = create_token(user["id"])
    return {"token": token, "user_id": user["id"], "username": user["username"]}


@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["id"],
        "username": user["username"],
        "has_api_keys": bool(user["encrypted_access_key"]),
        "discord_webhook_url": user["discord_webhook_url"] or "",
        "strategy": {
            "k": user["strategy_k"],
            "use_ma": bool(user["strategy_ma"]),
            "use_rsi": bool(user["strategy_rsi"]),
            "rsi_lower": user["strategy_rsi_lower"],
            "loss_pct": user["strategy_loss_pct"],
            "max_investment_krw": user["max_investment_krw"],
        },
    }


@router.post("/auth/api-keys")
async def save_api_keys(req: ApiKeysRequest, user: dict = Depends(get_current_user)):
    enc_access = encrypt_key(req.access_key)
    enc_secret = encrypt_key(req.secret_key)
    await update_user_keys(user["id"], enc_access, enc_secret)
    return {"message": "API keys saved"}


@router.post("/auth/discord")
async def save_discord(req: DiscordRequest, user: dict = Depends(get_current_user)):
    await update_user_discord(user["id"], req.webhook_url)
    return {"message": "Discord webhook saved"}


@router.post("/auth/strategy")
async def save_strategy(req: StrategyRequest, user: dict = Depends(get_current_user)):
    await update_user_strategy(user["id"], req.model_dump())
    return {"message": "Strategy saved"}
