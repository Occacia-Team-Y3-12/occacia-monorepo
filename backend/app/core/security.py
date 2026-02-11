import jwt  # This is the PyJWT library
from datetime import datetime, timedelta, timezone
from jwt.exceptions import PyJWTError as JWTError  # Alias for backward compatibility
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os

# 1. Initialize the Argon2 Hasher. 
# This is the industry gold standard for DevSecOps. 
# It's memory-hard, making it a nightmare for GPU cracking.
ph = PasswordHasher()

def get_password_hash(password: str) -> str:
    """Hashes a password using Argon2."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password; returns False if there's any mismatch or error."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False

# 2. Config Loading (ensure these are in your .env!)
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-emergency-fallback")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a secure JWT access token."""
    to_encode = data.copy()
    
    # Calculate expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    
    # PyJWT.encode returns a 'str', no more manual decoding needed
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt