from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings, logger
from middleware.logging_middleware import RequestLoggingMiddleware
from models.database import init_db
from models.schemas import ErrorResponse
from routes import api_router
from services.exceptions import AppException
from services.vector_service import get_vector_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]...")

    # 1. Initialize relational database schemas
    await init_db()

    # 2. Warm up vector store & ensure seed knowledge
    try:
        vs = get_vector_service()
        logger.info(f"Vector store initialized (collection: '{vs.collection_name}')")
    except Exception as e:
        logger.warning(f"Vector store initialization notice: {e}")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-ready Lenny Growth Assistant Backend API.\n\n"
        "Features:\n"
        "- Session-based conversational memory (`session_id`)\n"
        "- Dual LLM inference (OpenAI + Ollama)\n"
        "- Chroma Vector DB retrieval-augmented generation\n"
        "- Strict Pydantic v2 schemas\n"
        "- Structured logging middleware and global exception handling"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Error Handlers
# ==============================================================================
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handles all domain-specific application exceptions."""
    logger.warning(f"AppException [{exc.code}] on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.message,
            detail=exc.detail,
            code=exc.code,
            timestamp=datetime.now(timezone.utc),
        ).model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles request body and parameter validation errors (HTTP 422)."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error="Request validation failed",
            detail=exc.errors(),
            code="VALIDATION_ERROR",
            timestamp=datetime.now(timezone.utc),
        ).model_dump(mode="json"),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles standard FastAPI/Starlette HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=str(exc.detail),
            detail=exc.detail,
            code=f"HTTP_{exc.status_code}",
            timestamp=datetime.now(timezone.utc),
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catches all unexpected internal server errors (HTTP 500)."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error="An unexpected internal server error occurred.",
            detail=str(exc) if settings.DEBUG else None,
            code="INTERNAL_SERVER_ERROR",
            timestamp=datetime.now(timezone.utc),
        ).model_dump(mode="json"),
    )


# ==============================================================================
# Routes Registration
# ==============================================================================
# Mount root routes (/health, /chat)
app.include_router(api_router)

# Mount prefix routes (/api/v1/health, /api/v1/chat) for reverse proxy compatibility
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "chat": "/chat",
        "router": "/router",
        "artifacts": "/artifacts/generate",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
