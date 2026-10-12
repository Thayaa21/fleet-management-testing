"""FastAPI application factory.

Run from the backend/ directory:
    uvicorn app.main:app --reload --port 8000
"""
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import SessionLocal
from app.errors import register_error_handlers
from app.routers import (
    api_public,
    audit,
    auth,
    billing,
    customers,
    drivers,
    equipment,
    exceptions,
    integrations,
    locations,
    manifests,
    milestones,
    pickups,
    shipments,
    telematics,
    trips,
)
from app.services.audit import register_audit_listeners, set_audit_context

# Attach audit ORM hooks to the app's session factory once at import time.
register_audit_listeners(SessionLocal)

logger = logging.getLogger("tms")

REQUEST_ID_HEADER = "X-Request-ID"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.2.0")

    # ── Request ID middleware ──
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        # Seed the audit context with the request id; the auth dependency fills
        # in the actor once the user is resolved.
        set_audit_context(actor_type="system", actor_id=None, request_id=request_id)
        logger.info("request", extra={"request_id": request_id, "path": request.url.path, "method": request.method})
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )

    register_error_handlers(app)

    app.include_router(auth.router)
    app.include_router(customers.router)
    app.include_router(locations.router)
    app.include_router(drivers.router)
    app.include_router(equipment.router)
    app.include_router(shipments.router)
    app.include_router(milestones.router)
    app.include_router(audit.router)
    app.include_router(pickups.router)
    app.include_router(trips.router)
    app.include_router(manifests.router)
    app.include_router(telematics.ingest_router)
    app.include_router(telematics.logs_router)
    app.include_router(telematics.router)
    app.include_router(api_public.router)
    app.include_router(integrations.router)
    app.include_router(exceptions.router)
    app.include_router(billing.router)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "service": "tms-backend"}

    # ── Background webhook delivery worker ──
    @app.on_event("startup")
    async def _start_webhook_worker():
        import asyncio

        async def loop():
            from app.db import SessionLocal as _SL
            from app.services.webhooks import deliver_pending
            while True:
                await asyncio.sleep(20)
                try:
                    db = _SL()
                    try:
                        deliver_pending(db)
                    finally:
                        db.close()
                except Exception:  # noqa: BLE001 — worker must not crash the app
                    logger.exception("webhook worker pass failed")

        app.state.webhook_task = asyncio.create_task(loop())

    return app


app = create_app()
