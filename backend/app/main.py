import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import init_db
from app.services.vector_store import get_vector_store
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    setup_logging()
    logger.info("Initializing Lenny Growth Assistant Backend...")

    # Initialize relational database schemas
    await init_db()

    # Pre-warm Vector Store & Seed default growth playbook
    try:
        store = get_vector_store()
        logger.info(f"ChromaDB ready with collection: {store.collection_name}")
    except Exception as e:
        logger.warning(f"ChromaDB initialization notice: {e}")

    logger.info("Lenny Growth Assistant Backend successfully initialized.")
    yield
    # --- Shutdown ---
    logger.info("Shutting down Lenny Growth Assistant Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "Production-ready backend API for Lenny Growth Assistant. "
        "Powered by FastAPI, PostgreSQL (Supabase compatible), Chroma Vector DB, "
        "and dual LLM orchestration (OpenAI + Ollama)."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS if isinstance(settings.ALLOWED_CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Adds X-Process-Time response header for performance monitoring."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }


# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check server logs."},
    )
