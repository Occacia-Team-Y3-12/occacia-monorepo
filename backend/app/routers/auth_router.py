from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import PyJWTError as JWTError # The Alias for clean catch-alls
from datetime import timedelta

# Internal Imports
from app.core.database import get_db
from app.schemas.auth_schema import RegisterRequest
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services import vendor_service
from app.core.security import verify_password, create_access_token, SECRET_KEY, ALGORITHM
from app.services.auth_service import auth_service

# 1. SETUP ROUTER & AUTH SCHEME
router = APIRouter(prefix="/auth", tags=["Authentication"])

# The Token Entry Point
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/vendors/login")

# ==========================================
# 👮‍♂️ THE SECURITY GUARD (Dependency)
# ==========================================

def get_current_vendor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Validates the Digital ID Card (JWT).
    If the signature is wrong or the user is a ghost, throw 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # We use the ALGORITHM imported from security.py
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError: # This now catches ALL PyJWT related errors (expired, invalid, etc.)
        raise credentials_exception
    
    # Check the DB: Does the email on the ID card belong to a real vendor?
    vendor = vendor_service.get_vendor_by_email(db, email=email)
    if vendor is None:
        raise credentials_exception
        
    return vendor

# ==========================================
# 🚀 ROUTES
# ==========================================

# 1. REGISTER (Public)
@router.post("/vendors/register", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def register_vendor(vendor_data: VendorRegisterRequest, db: Session = Depends(get_db)):
    # Check for Duplicate Email
    if vendor_service.get_vendor_by_email(db, email=vendor_data.email):
        raise HTTPException(status_code=400, detail="This email is already taken!")
    
    # Check for Duplicate Display Name
    if vendor_service.get_vendor_by_display_name(db, name=vendor_data.display_name):
        raise HTTPException(status_code=400, detail="Business name already in use!")

    return vendor_service.create_vendor(db, vendor_data)

@router.post("/customers/register", status_code=201)
def register(payload: RegisterRequest):
    # payload will be CustomerRegister OR VendorRegister automatically
    return register(payload)

# 2. LOGIN (Public)
@router.post("/vendors/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find the user
    vendor = vendor_service.get_vendor_by_email(db, email=form_data.username)
    
    # Password Verification (Now using Argon2 under the hood in security.py)
    if not vendor or not verify_password(form_data.password, vendor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the Token
    access_token = create_access_token(
        data={"sub": vendor.email},
        expires_delta=timedelta(minutes=60)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# 3. GET CURRENT USER (Protected 🔒)
@router.get("/vendors/me", response_model=VendorResponse)
def read_users_me(current_vendor = Depends(get_current_vendor)):
    return current_vendor