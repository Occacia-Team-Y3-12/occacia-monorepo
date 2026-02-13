import jwt  # This is PyJWT, not jose!
from datetime import datetime, timedelta, timezone
from jwt.exceptions import PyJWTError as JWTError # Alias so your other files don't break
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os

# 1. THE LOCK: Argon2 is the DevSecOps gold standard.
# It is memory-hard, making GPU-based brute-force attacks nearly impossible.
ph = PasswordHasher()

def get_password_hash(password: str) -> str:
    """Hashes a password using Argon2 with automatic salting."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies an Argon2 hash. Returns False on mismatch or tampering."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False

# 2. THE BRAIN: Loading configuration from the environment.
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# FAIL-FAST: If the secret key is missing, kill the app. 
# Don't run a secure app with a 'None' key!
if not SECRET_KEY:
    raise RuntimeError("❌ CRITICAL: SECRET_KEY is missing from environment!")

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a secure, signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    
    # PyJWT returns a string directly, no more .decode('utf-8') hacks.
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)