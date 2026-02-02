import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

# Setup logger for this module
logger = logging.getLogger(__name__)

def add_exception_handlers(app: FastAPI):
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # 1. Log the ACTUAL error (Internal use only)
        # This records the stack trace so you can debug it later.
        logger.error(f"🔥 Global Exception: {exc}", exc_info=True)
        
        # 2. Return a clean, safe response to the user
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred. Our team has been notified.",
                "path": request.url.path
            }
        )