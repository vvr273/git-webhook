from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.core.config import get_settings
from app.core.security import verify_github_signature
from app.integrations.github.service import process_github_webhook

router = APIRouter(prefix="/webhooks", tags=["github-webhooks"])


@router.post("/github")
async def receive_github_webhook(request: Request, db: Session = Depends(get_db_session)) -> dict:
    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    event_type = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")

    if not verify_github_signature(raw_body, signature, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if not event_type or not delivery_id:
        raise HTTPException(status_code=400, detail="Missing required GitHub headers")

    return process_github_webhook(raw_body=raw_body, event_type=event_type, delivery_id=delivery_id, db=db)
