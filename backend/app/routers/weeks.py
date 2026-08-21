from fastapi import APIRouter

from shared.db import read_rows

router = APIRouter()


@router.get("/weeks")
def list_weeks() -> list[str]:
    rows = read_rows("ingest_log")
    return sorted({r["iso_week"] for r in rows}, reverse=True)
