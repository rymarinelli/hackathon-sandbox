import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from redis.asyncio import Redis
from redis.exceptions import RedisError

from gateway.logging_setup import configure_logging
from gateway.otel import configure_tracing
from gateway.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def create_redis_client(settings: Settings) -> Optional[Redis]:
    if not settings.redis_url:
        return None

    return Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=settings.request_timeout_s)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)
    tracer_provider = configure_tracing(settings)
    LoggingInstrumentor().instrument(set_logging_format=True)
    RedisInstrumentor().instrument()

    app = FastAPI(title=settings.app_name)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    @app.on_event("startup")
    async def _startup() -> None:
        app.state.settings = settings
        app.state.redis = create_redis_client(settings)
        if app.state.redis:
            try:
                await asyncio.wait_for(app.state.redis.ping(), timeout=settings.request_timeout_s)
                logger.info("Connected to Redis", extra={"url": settings.redis_url})
            except (RedisError, asyncio.TimeoutError) as exc:
                logger.warning("Unable to ping Redis on startup", extra={"error": str(exc)})

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        redis: Optional[Redis] = getattr(app.state, "redis", None)
        if redis:
            await redis.close()

    @app.get("/healthz", tags=["internal"])
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "service": settings.app_name})

    @app.get("/readyz", tags=["internal"])
    async def ready() -> JSONResponse:
        redis_ready = True
        redis_client: Optional[Redis] = getattr(app.state, "redis", None)
        if redis_client:
            try:
                await asyncio.wait_for(redis_client.ping(), timeout=settings.request_timeout_s)
            except (RedisError, asyncio.TimeoutError):
                redis_ready = False

        if settings.ready_requires_redis and not redis_ready:
            raise HTTPException(status_code=503, detail="Redis dependency not ready")

        return JSONResponse({"status": "ok", "redis": redis_ready})

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "gateway.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
