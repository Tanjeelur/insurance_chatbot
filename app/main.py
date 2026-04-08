import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logger import setup_logger, get_logger
from app.api.v1.endpoints import coverage

# Boot logger before anything else
setup_logger()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info("→ %s %s  (client: %s)", request.method, request.url.path, request.client.host)
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info("← %s %s  status=%s  %.0fms", request.method, request.url.path, response.status_code, elapsed)
    return response


@app.on_event("startup")
async def on_startup():
    logger.info("=" * 60)
    logger.info("  %s  v%s", settings.PROJECT_NAME, settings.PROJECT_VERSION)
    logger.info("  Model : %s", settings.OPENAI_MODEL)
    logger.info("  Prefix: %s", settings.API_V1_STR)
    logger.info("=" * 60)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Server shutting down.")


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Insurance Chatbot API"}


# Include API router
app.include_router(coverage.router, prefix=settings.API_V1_STR, tags=["coverage"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)