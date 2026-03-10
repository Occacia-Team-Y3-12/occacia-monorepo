import secrets
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT
from app.core.config import settings

# ==========================================
# 🔐 HASHER CONFIGURATION
# ==========================================

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    _hasher = PasswordHasher()
    _hasher_kind = "argon2"
except ModuleNotFoundError:
    try:
        from passlib.context import CryptContext

        _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        _hasher_kind = "bcrypt"
    except ModuleNotFoundError as e:  # pragma: no cover
        raise ModuleNotFoundError(
            "Missing password hashing dependency. Install 'argon2-cffi' (preferred) "
            "or 'passlib[bcrypt]'."
        ) from e


# ==========================================
# 🛠️ PASSWORD HELPERS
# ==========================================

def get_password_hash(password: str) -> str:
    """Scrambles a plain text password into a secure hash."""
    if _hasher_kind == "argon2":
        return _hasher.hash(password)
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a stored hash."""
    if _hasher_kind == "argon2":
        try:
            return _hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, Exception):
            return False
    return _pwd_context.verify(plain_password, hashed_password)


# ==========================================
# 🎫 TOKEN UTILITIES
# ==========================================

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a standard JWT access token for login."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a JWT refresh token for session continuation."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodes and validates a JWT token."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def generate_reset_token() -> str:
    """
    UC-07: Generates a secure, random, URL-safe string.
    This acts as the unique 'one-time key' for password resets.
    """
    return secrets.token_urlsafe(32)
