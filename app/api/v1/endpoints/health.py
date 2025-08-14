# app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from datetime import datetime
import logging
import os

from app.models.schemas import HealthResponse
from app.services.session_service import SessionService
from app.services.openai_service import OpenAIService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency injection
def get_session_service() -> SessionService:
    return SessionService()

# Global service instances
session_service = SessionService()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the application"
)
async def health_check():
    """
    Perform a basic health check of the application.
    
    Returns:
    - Application status
    - Current timestamp
    - Active sessions count
    - Application version
    """
    
    try:
        active_sessions = session_service.get_active_sessions_count()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            active_sessions=active_sessions,
            version=settings.VERSION
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            active_sessions=0,
            version=settings.VERSION
        )


@router.get(
    "/detailed",
    summary="Detailed health check",
    description="Perform a detailed health check including external service connectivity"
)
async def detailed_health_check():
    """
    Perform a detailed health check including:
    - Application status
    - OpenAI API connectivity
    - Session service status
    - Configuration status
    """
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.VERSION,
        "components": {}
    }
    
    # Check session service
    try:
        active_sessions = session_service.get_active_sessions_count()
        health_status["components"]["session_service"] = {
            "status": "healthy",
            "active_sessions": active_sessions,
            "max_sessions": session_service._max_sessions
        }
    except Exception as e:
        health_status["components"]["session_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check OpenAI configuration
    try:
        if settings.OPENAI_API_KEY:
            openai_service = OpenAIService()
            model_info = openai_service.get_model_info()
            health_status["components"]["openai_service"] = {
                "status": "configured",
                "model_info": model_info
            }
        else:
            health_status["components"]["openai_service"] = {
                "status": "not_configured",
                "error": "OpenAI API key not provided"
            }
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["components"]["openai_service"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check configuration
    try:
        health_status["components"]["configuration"] = {
            "status": "loaded",
            "debug": settings.DEBUG,
            "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
            "session_timeout": settings.SESSION_TIMEOUT
        }
    except Exception as e:
        health_status["components"]["configuration"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if the application is ready to serve requests"
)
async def readiness_check():
    """
    Check if the application is ready to serve requests.
    
    This endpoint is useful for container orchestration systems
    to determine when the application is ready to receive traffic.
    """
    
    try:
        # Check essential services
        if not settings.OPENAI_API_KEY:
            return {
                "status": "not_ready",
                "reason": "OpenAI API key not configured"
            }
        
        # Test session service
        _ = session_service.get_active_sessions_count()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "status": "not_ready",
            "reason": str(e)
        }


@router.get(
    "/live",
    summary="Liveness check",
    description="Check if the application is alive and responsive"
)
async def liveness_check():
    """
    Basic liveness check for container orchestration.
    
    This endpoint should always return quickly and indicates
    that the application process is alive and responding.
    """
    
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "pid": os.getpid()
    }