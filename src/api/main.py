import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from src.core.config import get_settings
from src.core.logging_config import setup_logging, get_logger
from src.api.routes import tasks, rag

settings = get_settings()

# Setup logging
setup_logging(
    level=settings.log_level,
    json_format=(settings.log_format == "json"),
    service_name="rag-api",
)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Production-ready RAG Pipeline with FastAPI and Celery",
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    start_time = time.time()

    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        f"Request completed: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    return response


# Include routers
app.include_router(tasks.router)
app.include_router(rag.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "RAG Pipeline API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "timestamp": time.time(),
    }
