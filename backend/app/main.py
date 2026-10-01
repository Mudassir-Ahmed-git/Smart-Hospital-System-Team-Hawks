import logging

from fastapi import APIRouter, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.config import settings
from app.database.session import SessionLocal
from app.models.user import User
from app.routers import ai, analytics, auth, beds, emergency, hospitals, patients, referrals
from app.services.notification_service import manager
from app.utils.security import decode_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

DESCRIPTION = """
Real-time hospital bed, ICU and emergency capacity management.

**Quick start:** call `POST /api/auth/login` (demo users are created by the seed script), then press
**Authorize** and paste the token. Roles: `patient`, `hospital` (staff), `ambulance` (coordinator), `admin`.
"""

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, description=DESCRIPTION,
              docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

api = APIRouter(prefix=settings.API_PREFIX)
for module in (auth, hospitals, beds, patients, emergency, referrals, analytics, ai):
    api.include_router(module.router)


@api.websocket("/ws/capacity")
async def capacity_socket(ws: WebSocket, token: str, hospital_id: int | None = None):
    """Live events: capacity_updated, new_request, status_changed. Connect with ?token=<JWT>[&hospital_id=N]."""
    try:
        payload = decode_token(token)
        with SessionLocal() as db:
            user = db.get(User, int(payload["sub"]))
    except Exception:
        user = None
    if user is None:
        await ws.close(code=4401)
        return
    if user.role == "hospital":
        hospital_id = user.hospital_id  # staff only receive their own hospital's events
    await manager.connect(ws, hospital_id)
    try:
        while True:
            await ws.receive_text()  # keep-alive; clients may send pings
    except WebSocketDisconnect:
        manager.disconnect(ws)


app.include_router(api)


@app.get("/health", tags=["System"], summary="Liveness + DB check")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "up"}
    except Exception:
        return JSONResponse({"status": "degraded", "database": "down"}, status_code=503)


@app.get("/", include_in_schema=False)
def root():
    return {"name": settings.APP_NAME, "docs": "/docs", "health": "/health"}


# ---------------------------------------------------------------- error handling
@app.exception_handler(IntegrityError)
async def integrity_error(_: Request, exc: IntegrityError):
    log.warning("integrity error: %s", exc.orig)
    return JSONResponse({"detail": "The request conflicts with existing data."}, status_code=409)


@app.exception_handler(OperationalError)
async def db_down(_: Request, exc: OperationalError):
    log.error("database error: %s", exc)
    return JSONResponse({"detail": "Database temporarily unavailable. Please retry."}, status_code=503)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse({"detail": "Internal server error"}, status_code=500)
