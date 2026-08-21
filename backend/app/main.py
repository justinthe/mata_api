import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.routers import alerts, boundaries, cells, fire, ingest_status, landslide, reports, weeks
from shared.db import get_connection

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("FRONTEND_ORIGIN", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/generated", StaticFiles(directory="generated"), name="generated")
app.include_router(weeks.router)
app.include_router(boundaries.router)
app.include_router(fire.router)
app.include_router(landslide.router)
app.include_router(alerts.router)
app.include_router(cells.router)
app.include_router(ingest_status.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    try:
        engine = get_connection()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"db": "ok"}
    except Exception:
        return JSONResponse(status_code=503, content={"db": "unreachable"})
