from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings, validate_runtime_security_settings, build_cors_origins
from app.core.database import engine, text_to_sql_engine, Base, async_session
from app.core.errors import CORRELATION_ID_RE, correlation_id_from_request, public_error_detail
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
from app.api.evaluations import router as evaluations_router
from app.api.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend...")
    validate_runtime_security_settings(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        from app.llm.vector_store import ensure_pgvector_schema
        if await ensure_pgvector_schema():
            logger.info("pgvector document index ready")
    except Exception as exc:
        logger.warning(f"pgvector setup skipped: {exc}")
    logger.info("Database tables ready")

    # Ensure super admin exists
    async with async_session() as db:
        from app.services.user_service import ensure_super_admin
        await ensure_super_admin(db, settings.SUPER_ADMIN_EMAIL, settings.SUPER_ADMIN_PASSWORD)
        logger.info(f"Super admin ensured: {settings.SUPER_ADMIN_EMAIL}")

    yield

    await engine.dispose()
    if text_to_sql_engine is not None:
        await text_to_sql_engine.dispose()
    logger.info(f"{settings.PROJECT_NAME} backend shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(settings),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    supplied_id = request.headers.get("x-correlation-id", "")
    if supplied_id and CORRELATION_ID_RE.fullmatch(supplied_id):
        request.state.correlation_id = supplied_id
    else:
        correlation_id_from_request(request)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    return response


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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    correlation_id = correlation_id_from_request(request)
    logger.exception("Unhandled API error correlation_id=%s", correlation_id)
    return JSONResponse(
        status_code=500,
        content={"detail": public_error_detail(request, "Internal server error.", exc)},
        headers={"X-Correlation-ID": correlation_id},
    )


app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(companies_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(faq_router, prefix=settings.API_PREFIX)
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(datasets_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(status_router, prefix=settings.API_PREFIX)
app.include_router(evaluations_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)

install_access_log_probe_filter()


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}
