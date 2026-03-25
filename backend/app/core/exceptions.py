from asgi_correlation_id import correlation_id
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "global.exception",
            error=str(exc),
            path=request.url.path,
            request_id=correlation_id.get(),
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred. Our team has been notified.",
                "path": request.url.path
            }
        )
