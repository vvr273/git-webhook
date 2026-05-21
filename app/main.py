from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.bot_detection import is_bot_actor
from app.config import get_settings
from app.database import get_db_session, get_engine
from app.models import Base, GitHubEvent
from app.normalizers import normalize_github_event
from app.security import verify_github_signature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("github_webhooks")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(title="GitHub Webhook Testing Service", version="0.1.0", lifespan=lifespan)


def _serialize_event(model: GitHubEvent) -> dict[str, Any]:
    return {
        "id": model.id,
        "delivery_id": model.delivery_id,
        "event_type": model.event_type,
        "action": model.action,
        "repository_full_name": model.repository_full_name,
        "actor_login": model.actor_login,
        "actor_type": model.actor_type,
        "is_bot": model.is_bot,
        "occurred_at": model.occurred_at.astimezone(UTC).isoformat().replace("+00:00", "Z") if model.occurred_at else None,
        "received_at": model.received_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "normalized_payload": model.normalized_payload,
        "raw_payload": model.raw_payload,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/github")
async def receive_github_webhook(request: Request, db: Session = Depends(get_db_session)) -> dict[str, Any]:
    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    event_type = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")

    if not verify_github_signature(raw_body, signature, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if not event_type or not delivery_id:
        raise HTTPException(status_code=400, detail="Missing required GitHub headers")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    normalized = normalize_github_event(delivery_id=delivery_id, event_type=event_type, payload=payload)
    actor = normalized.get("actor") or {}
    repository = normalized.get("repository") or {}
    occurred_at_raw = normalized.get("occurred_at")
    occurred_at = None
    if occurred_at_raw:
        occurred_at = datetime.fromisoformat(occurred_at_raw.replace("Z", "+00:00")).astimezone(UTC)

    event = GitHubEvent(
        delivery_id=delivery_id,
        event_type=event_type,
        action=normalized.get("action"),
        repository_full_name=repository.get("full_name"),
        actor_login=actor.get("login"),
        actor_type=actor.get("type"),
        is_bot=is_bot_actor(actor.get("login"), actor.get("type")),
        occurred_at=occurred_at,
        normalized_payload=normalized,
        raw_payload=payload if settings.store_raw_payload else None,
    )

    try:
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(
            "Stored GitHub webhook delivery_id=%s event_type=%s repository=%s actor_login=%s",
            delivery_id,
            event_type,
            repository.get("full_name"),
            actor.get("login"),
        )
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(GitHubEvent).where(GitHubEvent.delivery_id == delivery_id))
        if existing is None:
            raise HTTPException(status_code=409, detail="Duplicate delivery ID could not be resolved")
        return {"status": "duplicate", "delivery_id": delivery_id, "event_type": existing.event_type}

    return {"status": "accepted", "delivery_id": delivery_id, "event_type": event_type}


@app.get("/events")
async def list_events(db: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    events = db.scalars(select(GitHubEvent).order_by(GitHubEvent.received_at.desc())).all()
    return [_serialize_event(event) for event in events]


@app.get("/events/{delivery_id}")
async def get_event(delivery_id: str, db: Session = Depends(get_db_session)) -> dict[str, Any]:
    event = db.scalar(select(GitHubEvent).where(GitHubEvent.delivery_id == delivery_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _serialize_event(event)


@app.get("/metrics/summary")
async def metrics_summary(db: Session = Depends(get_db_session)) -> dict[str, Any]:
    total_events = db.scalar(select(func.count()).select_from(GitHubEvent)) or 0

    events_by_type_rows = db.execute(
        select(GitHubEvent.event_type, func.count()).group_by(GitHubEvent.event_type)
    ).all()
    events_by_repository_rows = db.execute(
        select(GitHubEvent.repository_full_name, func.count()).group_by(GitHubEvent.repository_full_name)
    ).all()

    bot_events = db.scalar(select(func.count()).select_from(GitHubEvent).where(GitHubEvent.is_bot.is_(True))) or 0
    human_events = db.scalar(select(func.count()).select_from(GitHubEvent).where(GitHubEvent.is_bot.is_(False))) or 0
    pull_requests_opened = db.scalar(
        select(func.count()).select_from(GitHubEvent).where(
            GitHubEvent.event_type == "pull_request",
            GitHubEvent.action == "opened",
        )
    ) or 0
    pull_requests_merged = db.scalar(
        select(func.count()).select_from(GitHubEvent).where(
            GitHubEvent.event_type == "pull_request",
            GitHubEvent.action == "closed",
            func.json_extract(GitHubEvent.normalized_payload, "$.metadata.merged") == 1,
        )
    ) or 0
    pushes = db.scalar(
        select(func.count()).select_from(GitHubEvent).where(GitHubEvent.event_type == "push")
    ) or 0
    workflow_runs_completed = db.scalar(
        select(func.count()).select_from(GitHubEvent).where(
            GitHubEvent.event_type == "workflow_run",
            func.json_extract(GitHubEvent.normalized_payload, "$.metadata.conclusion").is_not(None),
        )
    ) or 0

    return {
        "total_events": total_events,
        "events_by_type": {row[0]: row[1] for row in events_by_type_rows if row[0] is not None},
        "events_by_repository": {row[0]: row[1] for row in events_by_repository_rows if row[0] is not None},
        "bot_events": bot_events,
        "human_events": human_events,
        "pull_requests_opened": pull_requests_opened,
        "pull_requests_merged": pull_requests_merged,
        "pushes": pushes,
        "workflow_runs_completed": workflow_runs_completed,
    }
