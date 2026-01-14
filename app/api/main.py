from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response, JSONResponse

from app.api.v1.router import api_router
from app.observability.logging import configure_logging
from app.observability.middleware import ObservabilityMiddleware
from app.observability.metrics import start_metrics_json_dumper
from app.observability.hawk import init_hawk, capture_exception


configure_logging()

app = FastAPI(title="web lab1")

app.add_middleware(ObservabilityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_hawk(app)

@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


start_metrics_json_dumper()

app.include_router(api_router, prefix="/api/v1")


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "ok"}
