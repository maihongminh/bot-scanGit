"""API routes"""
from fastapi import APIRouter

from .repos import router as repos_router
from .detections import router as detections_router
from .stats import router as stats_router
from .scan import router as scan_router

# Create main router
api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(repos_router, prefix="/repos", tags=["repositories"])
api_router.include_router(detections_router, prefix="/detections", tags=["detections"])
api_router.include_router(stats_router, prefix="/stats", tags=["statistics"])
api_router.include_router(scan_router, prefix="/scan", tags=["scanning"])

__all__ = ["api_router"]
