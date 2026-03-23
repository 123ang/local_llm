from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, async_session
from app.core.logger import logger, security_logger, install_access_log_probe_filter
from app.core.probe_detection import is_suspicious_probe_path

from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.users import router as users_router
from app.api.faq import router as faq_router
from app.api.documents import router as documents_router
from app.api.datasets import router as datasets_router
from app.api.chat import router as chat_router
from app.api.audit import router as audit_router
from app.api.status import router as status_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")

    # Ensure super admin exists
    async with async_session() as db:
        from app.services.user_service import ensure_super_admin
        await ensure_super_admin(db, settings.SUPER_ADMIN_EMAIL, settings.SUPER_ADMIN_PASSWORD)
        logger.info(f"Super admin ensured: {settings.SUPER_ADMIN_EMAIL}")

    yield

    await engine.dispose()
    logger.info(f"{settings.PROJECT_NAME} backend shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:3001",
]
if settings.CORS_EXTRA_ORIGINS:
    _cors_origins.extend(
        o.strip() for o in settings.CORS_EXTRA_ORIGINS.split(",") if o.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_probe_logger(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if is_suspicious_probe_path(path):
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "-")
        security_logger.info(
            f'probe_detected ip={client_ip} method={request.method} path="{path}" status={response.status_code} ua="{user_agent}"'
        )
    return response


app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(companies_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(faq_router, prefix=settings.API_PREFIX)
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(datasets_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(status_router, prefix=settings.API_PREFIX)

install_access_log_probe_filter()


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}
