from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from backend.auth import hash_password, verify_password, create_token, encrypt_key, get_current_user
from backend.database import (
    create_user, get_user_by_username, update_user_keys,
    update_user_discord, update_user_strategy, update_user_notify_settings,
)

router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    access_key: Optional[str] = None
    secret_key: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ApiKeysRequest(BaseModel):
    access_key: str
    secret_key: str


class DiscordRequest(BaseModel):
    webhook_url: str
    notify_buy: bool = True
    notify_sell: bool = True
    notify_error: bool = True
    notify_start_stop: bool = True


class StrategyRequest(BaseModel):
    k: float = 0.5
    use_ma: bool = True
    use_rsi: bool = True
    rsi_lower: float = 30.0
    loss_pct: float = 0.03
    take_profit_pct: float = 0.05
    max_investment_krw: float = 100000
    min_investment_krw: float = 5000
    strategy_type: str = "volatility_breakout"


@router.post("/auth/register")
async def register(req: RegisterRequest):
    if len(req.username) < 3:
        raise HTTPException(400, "아이디는 3자 이상이어야 합니다")
    if len(req.password) < 6:
        raise HTTPException(400, "비밀번호는 6자 이상이어야 합니다")

    existing = await get_user_by_username(req.username)
    if existing:
        raise HTTPException(400, "이미 사용 중인 아이디입니다")

    user_id = await create_user(req.username, hash_password(req.password))

    # API 키가 함께 제출된 경우 저장
    if req.access_key and req.secret_key:
        enc_access = encrypt_key(req.access_key)
        enc_secret = encrypt_key(req.secret_key)
        await update_user_keys(user_id, enc_access, enc_secret)

    token = create_token(user_id)
    return {"token": token, "user_id": user_id, "username": req.username}


@router.post("/auth/login")
async def login(req: LoginRequest):
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "아이디 또는 비밀번호가 올바르지 않습니다")

    token = create_token(user["id"])
    return {"token": token, "user_id": user["id"], "username": user["username"]}


@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["id"],
        "username": user["username"],
        "has_api_keys": bool(user["encrypted_access_key"]),
        "is_demo": bool(user.get("is_demo", 0)),
        "demo_balance": user.get("demo_balance", 10000000),
        "discord_webhook_url": user["discord_webhook_url"] or "",
        "notify_buy": bool(user.get("notify_buy", 1)),
        "notify_sell": bool(user.get("notify_sell", 1)),
        "notify_error": bool(user.get("notify_error", 1)),
        "notify_start_stop": bool(user.get("notify_start_stop", 1)),
        "strategy": {
            "k": user["strategy_k"],
            "use_ma": bool(user["strategy_ma"]),
            "use_rsi": bool(user["strategy_rsi"]),
            "rsi_lower": user["strategy_rsi_lower"],
            "loss_pct": user["strategy_loss_pct"],
            "max_investment_krw": user["max_investment_krw"],
            "min_investment_krw": user.get("min_investment_krw", 5000),
            "take_profit_pct": user.get("take_profit_pct", 0.05),
            "strategy_type": user.get("strategy_type", "volatility_breakout"),
        },
    }


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    password: str


@router.post("/auth/change-password")
async def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    if not verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(400, "현재 비밀번호가 올바르지 않습니다")
    if len(req.new_password) < 6:
        raise HTTPException(400, "새 비밀번호는 6자 이상이어야 합니다")

    from backend.database import update_user_password
    await update_user_password(user["id"], hash_password(req.new_password))
    return {"message": "비밀번호가 변경되었습니다"}


@router.post("/auth/delete-account")
async def delete_account(req: DeleteAccountRequest, user: dict = Depends(get_current_user)):
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(400, "비밀번호가 올바르지 않습니다")

    # 봇 중지
    from backend.engine import bot_manager
    bot = bot_manager.get_bot(user["id"])
    if bot:
        await bot.stop()
        bot_manager.bots.pop(user["id"], None)

    from backend.database import delete_user
    await delete_user(user["id"])
    return {"message": "계정이 삭제되었습니다"}


@router.post("/auth/api-keys")
async def save_api_keys(req: ApiKeysRequest, user: dict = Depends(get_current_user)):
    enc_access = encrypt_key(req.access_key)
    enc_secret = encrypt_key(req.secret_key)
    await update_user_keys(user["id"], enc_access, enc_secret)
    return {"message": "API 키 저장 완료"}


@router.post("/auth/discord")
async def save_discord(req: DiscordRequest, user: dict = Depends(get_current_user)):
    await update_user_discord(user["id"], req.webhook_url)
    await update_user_notify_settings(user["id"], req.notify_buy, req.notify_sell, req.notify_error, req.notify_start_stop)
    return {"message": "알림 설정 저장 완료"}


@router.post("/auth/strategy")
async def save_strategy(req: StrategyRequest, user: dict = Depends(get_current_user)):
    await update_user_strategy(user["id"], req.model_dump())
    return {"message": "전략 저장 완료"}
