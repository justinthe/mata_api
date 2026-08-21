from fastapi import APIRouter

from shared.db import read_rows

router = APIRouter()


@router.get("/ingest-status")
def ingest_status(week: str) -> list[dict]:
    rows = read_rows("ingest_log", {"iso_week": week})
    return [{"file_type": r["file_type"], "status": r["status"], "detail": r["detail"]} for r in rows]
