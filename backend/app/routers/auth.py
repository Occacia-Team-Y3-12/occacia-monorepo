from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import timedelta

# Internal Imports
from app.core.database import get_db
from app.schemas.vendor_schema import VendorRegisterRequest, VendorResponse
from app.services import vendor_service
from app.core.security import verify_password, create_access_token, SECRET_KEY, ALGORITHM

# 1. SETUP ROUTER & AUTH SCHEME
router = APIRouter(prefix="/auth", tags=["Authentication"])

# This tells FastAPI that the "Lock" uses the /login endpoint to get the key
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/vendors/login")

# ==========================================
# 👮‍♂️ THE SECURITY GUARD (Dependency)
# ==========================================
def get_current_vendor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decodes the JWT token and retrieves the logged-in vendor.
    If the token is fake/expired, it throws a 401 error.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the "Digital ID Card"
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if the user still exists in the database
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

# 2. LOGIN (Public)
@router.post("/vendors/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find the user
    vendor = vendor_service.get_vendor_by_email(db, email=form_data.username)
    
    # Verify Password
    if not vendor or not verify_password(form_data.password, vendor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the Token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": vendor.email},
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# 3. GET CURRENT USER (Protected 🔒)
@router.get("/vendors/me", response_model=VendorResponse)
def read_users_me(current_vendor = Depends(get_current_vendor)):
    """
    This route is LOCKED. Only users with a valid JWT can see this.
    It returns the profile of the currently logged-in vendor.
    """
    return current_vendor