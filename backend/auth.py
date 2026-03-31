import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from cryptography.fernet import Fernet

from backend.database import get_user_by_id

# JWT
SECRET_KEY = os.getenv("JWT_SECRET", "")
if not SECRET_KEY:
    import warnings
    SECRET_KEY = hashlib.sha256(os.urandom(32)).hexdigest()
    warnings.warn(
        "JWT_SECRET is not set! Generated a random key — all tokens will be "
        "invalidated on server restart. Set JWT_SECRET in .env for production.",
        stacklevel=1,
    )
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

# API key encryption
ENCRYPT_KEY = os.getenv("ENCRYPT_KEY", "")
if not ENCRYPT_KEY:
    import warnings
    ENCRYPT_KEY = Fernet.generate_key().decode()
    warnings.warn(
        "ENCRYPT_KEY is not set! Generated a random key — previously encrypted "
        "API keys will be unrecoverable after restart. Set ENCRYPT_KEY in .env.",
        stacklevel=1,
    )
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
