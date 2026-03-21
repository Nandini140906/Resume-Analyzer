"""
main.py - FastAPI application entry point.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import get_settings
from backend.logger import logger, setup_logger
from backend.utils.database import init_db
from backend.routes import resume_routes, job_routes, ranking_routes, export_routes

settings = get_settings()
setup_logger(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting Resume Analyzer API...")
    # Ensure upload dir exists
    import pathlib
    pathlib.Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path("logs").mkdir(exist_ok=True)
    # Init database
    await init_db()
    logger.info(f"API ready | env={settings.app_env} | ai_provider={settings.ai_provider}")
    yield
    logger.info("Shutting down Resume Analyzer API.")


app = FastAPI(
    title="Resume Analyzer API",
    description="AI-powered resume analysis, scoring, and candidate ranking system.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(resume_routes.router)
app.include_router(job_routes.router)
app.include_router(ranking_routes.router)
app.include_router(export_routes.router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0", "ai_provider": settings.ai_provider}


# ─── Global Exception Handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
