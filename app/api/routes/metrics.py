from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.integrations.github.service import get_events_summary

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
async def metrics_summary(db: Session = Depends(get_db_session)) -> dict[str, Any]:
    return get_events_summary(db)
