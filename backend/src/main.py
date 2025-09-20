"""
FastAPI Application Entry Point

This is the main application file that configures FastAPI with all
middleware, routes, and dependencies.

Educational comparison between FastAPI application setup and
Spring Boot @SpringBootApplication configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from settings import get_settings

# Get application settings
settings = get_settings()

# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Educational law firm people analytics API",
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "LegalAnalytics Mini API",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "debug": settings.debug,
    }


# API routes
from api.employees import router as employees_router
from api.time_entries import router as time_entries_router
from api.dashboard import router as dashboard_router
from api.upload import router as upload_router

app.include_router(employees_router, prefix=settings.api_v1_prefix)
app.include_router(time_entries_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(upload_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )