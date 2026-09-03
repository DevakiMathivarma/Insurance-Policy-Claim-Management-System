import asyncio

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import SessionLocal
from app.utils.logger import logger
from app.services.auth_service import create_default_admin

from app.routes.auth import router as auth_router
from app.routes.customers import router as customers_router
from app.routes.plans import router as plans_router
from app.routes.policies import router as policies_router
from app.routes.beneficiaries import router as beneficiaries_router
from app.routes.payments import router as payments_router
from app.routes.claims import router as claims_router
from app.routes.documents import router as documents_router
from app.routes.settlements import router as settlements_router
from app.routes.dashboard import router as dashboard_router
from app.routes.websocket import router as websocket_router, manager as websocket_manager

app = FastAPI(title="Insurance Policy & Claim Management System", version="1.0.0")


# ---------------------------------------------------------------------------
# CORS (level 15 requirement)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ---------------------------------------------------------------------------
# Global Exception Handling (level 15 requirement)
# ---------------------------------------------------------------------------


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):

    logger.warning(f"HTTP {exc.status_code} : {exc.detail} : {request.method} {request.url.path}")

    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    logger.warning(f"Validation failed : {request.method} {request.url.path} : {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"message": "Validation failed.", "errors": exc.errors()})
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    logger.error(f"Unhandled exception : {request.method} {request.url.path} : {str(exc)}")

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "An unexpected error occurred."})


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------


@app.on_event("startup")
def startup():

    logger.info("Application starting.")

    db = SessionLocal()

    try:

        create_default_admin(db)

    finally:

        db.close()

    logger.info("Application started successfully.")


# captures the real, running event loop so synchronous service functions
# can safely push websocket broadcasts from a background thread - same
# fix learned from the travel and property platforms' websocket features
@app.on_event("startup")
async def capture_event_loop():

    websocket_manager.set_loop(asyncio.get_running_loop())


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/")
def root():

    return {"message": "Insurance Policy & Claim Management System API", "docs": "/docs"}


@app.get("/health")
def health_check():

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(plans_router)
app.include_router(policies_router)
app.include_router(beneficiaries_router)
app.include_router(payments_router)
app.include_router(claims_router)
app.include_router(documents_router)
app.include_router(settlements_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)