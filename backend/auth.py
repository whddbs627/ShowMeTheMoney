import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from cryptography.fernet import Fernet

from backend.database import get_user_by_id

# JWT - 환경변수가 없으면 랜덤 생성 (서버 재시작 시 기존 토큰 무효화)
SECRET_KEY = os.getenv("JWT_SECRET") or hashlib.sha256(os.urandom(32)).hexdigest()
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

# API key encryption
ENCRYPT_KEY = os.getenv("ENCRYPT_KEY", "")
if not ENCRYPT_KEY:
    ENCRYPT_KEY = Fernet.generate_key().decode()
fernet = Fernet(ENCRYPT_KEY.encode() if isinstance(ENCRYPT_KEY, str) else ENCRYPT_KEY)

security = HTTPBearer()


def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt_hex, key_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 100000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def encrypt_key(plain: str) -> str:
    return fernet.encrypt(plain.encode()).decode()


def decrypt_key(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
