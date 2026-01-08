import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from jose import JWTError, ExpiredSignatureError
from app.database import engine, Base
from app.routers import auth

# ==========================================
# 1. SETUP LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ==========================================
# 2. INITIALIZE DATABASE
# ==========================================
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. CONFIGURE FASTAPI
# ==========================================
app = FastAPI(
    title="Occacia API",
    version="1.0.0",
    docs_url="/docs",
    exception_handlers={} # Disable default handlers
)

# ==========================================
# 🧠 UNIFIED RESPONSE FORMATTER
# ==========================================
def create_error_response(status_code: int, message: str, details: str = None, path: str = ""):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": status_code,
                "type": "error",
                "message": message,
                "details": details,
                "path": path,
                "timestamp": time.time()
            }
        },
    )

# ==========================================
# 🛡️ GLOBAL ERROR HANDLERS
# ==========================================

# 1. DUPLICATE DATA (409 CONFLICT) - CRITICAL FOR REGISTRATION
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    error_info = str(exc.orig) if exc.orig else str(exc)
    detail_msg = "Data conflict occurred."
    
    if "unique constraint" in error_info.lower():
        detail_msg = "A record with this Email or Display Name already exists."
    
    return create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        message="Duplicate Entry",
        details=detail_msg,
        path=request.url.path
    )

# 2. AUTHENTICATION ERRORS (401) - CRITICAL FOR SECURITY
@app.exception_handler(JWTError)
async def jwt_error_handler(request: Request, exc: JWTError):
    return create_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message="Invalid Token",
        details="Your authentication token is corrupt or invalid.",
        path=request.url.path
    )

@app.exception_handler(ExpiredSignatureError)
async def expired_token_handler(request: Request, exc: ExpiredSignatureError):
    return create_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message="Token Expired",
        details="Your session has ended. Please login again.",
        path=request.url.path
    )

# 3. VALIDATION ERRORS (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        loc = error.get("loc")
        field = ".".join(str(x) for x in loc) if loc else "field"
        msg = error.get("msg")
        error_messages.append(f"{field}: {msg}")
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation Failed",
        details=error_messages,
        path=request.url.path
    )

# 4. NOT FOUND & METHOD NOT ALLOWED (404/405)
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return create_error_response(404, "Resource Not Found", "The URL does not exist.", request.url.path)

@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    return create_error_response(405, "Method Not Allowed", f"Method {request.method} not allowed.", request.url.path)

# 5. LOGIC & DATABASE ERRORS
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return create_error_response(exc.status_code, exc.detail, path=request.url.path)

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"💾 DB ERROR: {str(exc)}")
    return create_error_response(503, "Database Unavailable", "Service temporarily down.", request.url.path)

# 6. CATCH-ALL CRASH PAD (500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 CRITICAL ERROR: {str(exc)}", exc_info=True)
    return create_error_response(500, "Internal Server Error", "An unexpected error occurred.", request.url.path)

# ==========================================
# 🚀 ROUTERS
# ==========================================
app.include_router(auth.router)

@app.get("/")
def health_check():
    return {"success": True, "message": "Occacia Backend Operational", "env": "dev"}