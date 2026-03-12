import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global Exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred. Our team has been notified.",
                "path": request.url.path
            }
        )