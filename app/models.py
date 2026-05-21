from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GitHubEvent(Base):
    __tablename__ = "github_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    delivery_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    repository_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    actor_login: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    actor_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    normalized_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
