"""
FastAPI Application Entrypoint for 3GPP-Grounded-RAG API.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routes import router as api_router
from api.dependencies import get_rag_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rag_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
    logger.info("Starting up 3GPP-Grounded-RAG API Service...")
    try:
        service = get_rag_service()
        service.initialize()
        logger.info(
            f"RAG Service Ready: Embedding='{service.embed_model}', Generation='{service.gen_model}', "
            f"VectorStore Chunks={service.vector_store.count() if service.vector_store else 0}"
        )
    except Exception as e:
        logger.warning(f"RAG service deferred initialization notice: {e}")
    
    yield
    
    logger.info("Shutting down 3GPP-Grounded-RAG API Service...")


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    app = FastAPI(
        title="3GPP-Grounded-RAG API",
        version="1.0.0",
        description=(
            "Production-grade, grounded Question-Answering API for 3GPP 5G Technical Specifications. "
            "Features hybrid retrieval (Dense + BM25 + RRF), evidence gating, structured generation, "
            "authoritative citation validation, deterministic claim verification, and safe abstention."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    cors_env = os.getenv("CORS_ORIGINS", "*")
    origins: List[str] = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    if not origins:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Clean Exception Handlers preventing stack trace / path leakage
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Request validation error on {request.url.path}: {exc}")
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Invalid input")
            errors.append(f"{loc}: {msg}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Invalid request parameters: " + "; ".join(errors),
                "error_code": "VALIDATION_ERROR",
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": str(exc.detail),
                "error_code": f"HTTP_{exc.status_code}",
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal error occurred while processing your request.",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )

    # Include routes
    app.include_router(api_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api.main:app", host=host, port=port, reload=False)
