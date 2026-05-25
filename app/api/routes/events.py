from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.db.models import GitHubEvent
from app.integrations.github.service import serialize_github_event

router = APIRouter(tags=["events"])


@router.get("/events")
async def list_events(db: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    events = db.scalars(select(GitHubEvent).order_by(GitHubEvent.received_at.desc())).all()
    return [serialize_github_event(event) for event in events]


@router.get("/events/{delivery_id}")
async def get_event(delivery_id: str, db: Session = Depends(get_db_session)) -> dict[str, Any]:
    event = db.scalar(select(GitHubEvent).where(GitHubEvent.delivery_id == delivery_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return serialize_github_event(event)
