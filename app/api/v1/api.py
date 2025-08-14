from fastapi import APIRouter
from app.api.v1.endpoints import coverage

api_router = APIRouter()
api_router.include_router(coverage.router, tags=["coverage"])