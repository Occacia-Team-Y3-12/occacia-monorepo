import jwt  # Modern PyJWT
from datetime import datetime, timedelta, timezone
from jwt.exceptions import PyJWTError as JWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os

# Initialize the bouncer
# Argon2 is memory-hard; it's the gold standard for resisting GPU cracking.
ph = PasswordHasher()

# Grab secrets from environment - fail fast if missing
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    # A Systems Engineer never lets an app start without its brain.
    raise RuntimeError("❌ CRITICAL: SECRET_KEY is missing from environment variables!")

def get_password_hash(password: str) -> str:
    """Uses Argon2 to hash the password with an automatic salt."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Returns True if valid, False if wrong or tampered with."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a secure JWT for the user."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    
    # PyJWT returns a string directly
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)