from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate).astimezone(UTC)
    except ValueError:
        return None


def _isoformat_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _best_timestamp(event_type: str, payload: dict[str, Any]) -> str | None:
    candidates: list[str | None] = []
    if event_type == "push":
        candidates = [
            payload.get("head_commit", {}).get("timestamp"),
            payload.get("repository", {}).get("updated_at"),
        ]
    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        candidates = [pr.get("merged_at"), pr.get("closed_at"), pr.get("updated_at"), pr.get("created_at")]
    elif event_type == "pull_request_review":
        review = payload.get("review", {})
        candidates = [review.get("submitted_at"), review.get("updated_at"), review.get("created_at")]
    elif event_type == "pull_request_review_comment":
        comment = payload.get("comment", {})
        candidates = [comment.get("updated_at"), comment.get("created_at")]
    elif event_type == "workflow_run":
        run = payload.get("workflow_run", {})
        candidates = [run.get("updated_at"), run.get("run_started_at"), run.get("created_at")]
    elif event_type == "deployment":
        deployment = payload.get("deployment", {})
        candidates = [deployment.get("updated_at"), deployment.get("created_at")]
    elif event_type == "deployment_status":
        status = payload.get("deployment_status", {})
        candidates = [status.get("updated_at"), status.get("created_at")]
    else:
        candidates = [
            payload.get("repository", {}).get("updated_at"),
            payload.get("sender", {}).get("updated_at"),
        ]

    for candidate in candidates:
        parsed = _parse_dt(candidate)
        if parsed:
            return _isoformat_utc(parsed)
    return _isoformat_utc(datetime.now(UTC))


def _repository(payload: dict[str, Any]) -> dict[str, Any]:
    repo = payload.get("repository") or {}
    return {
        "id": repo.get("id"),
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "private": repo.get("private"),
    }


def _actor(payload: dict[str, Any], event_type: str) -> dict[str, Any]:
    if event_type == "deployment_status":
        creator = payload.get("deployment_status", {}).get("creator") or payload.get("sender") or {}
        return {"id": creator.get("id"), "login": creator.get("login"), "type": creator.get("type")}

    sender = payload.get("sender") or {}
    return {"id": sender.get("id"), "login": sender.get("login"), "type": sender.get("type")}


def _normalize_push(payload: dict[str, Any]) -> dict[str, Any]:
    commits = payload.get("commits") or []
    authors: set[str] = set()
    distinct_count = 0

    for commit in commits:
        if commit.get("distinct"):
            distinct_count += 1
        author = commit.get("author") or {}
        if author.get("name") and author.get("email"):
            authors.add(f"{author['name']} <{author['email']}>")
        elif author.get("email"):
            authors.add(author["email"])
        elif author.get("name"):
            authors.add(author["name"])
        elif author.get("username"):
            authors.add(author["username"])

    return {
        "branch": (payload.get("ref") or "").removeprefix("refs/heads/"),
        "commit_count": len(commits),
        "distinct_commit_count": distinct_count,
        "head_commit_id": payload.get("head_commit", {}).get("id"),
        "pusher_name": payload.get("pusher", {}).get("name"),
        "pusher_email": payload.get("pusher", {}).get("email"),
        "commit_authors": sorted(authors),
    }


def _normalize_pull_request(payload: dict[str, Any]) -> dict[str, Any]:
    pr = payload.get("pull_request") or {}
    return {
        "pr_number": payload.get("number") or pr.get("number"),
        "pr_id": pr.get("id"),
        "pr_state": pr.get("state"),
        "pr_author": (pr.get("user") or {}).get("login"),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "closed_at": pr.get("closed_at"),
        "merged_at": pr.get("merged_at"),
        "merged": pr.get("merged"),
        "additions": pr.get("additions"),
        "deletions": pr.get("deletions"),
        "changed_files": pr.get("changed_files"),
        "commits": pr.get("commits"),
        "base_branch": (pr.get("base") or {}).get("ref"),
        "head_branch": (pr.get("head") or {}).get("ref"),
        "requested_reviewers_count": len(pr.get("requested_reviewers") or []),
    }


def _normalize_pull_request_review(payload: dict[str, Any]) -> dict[str, Any]:
    review = payload.get("review") or {}
    pr = payload.get("pull_request") or {}
    return {
        "pr_number": payload.get("number") or pr.get("number"),
        "review_id": review.get("id"),
        "review_state": review.get("state"),
        "submitted_at": review.get("submitted_at"),
        "reviewer_login": (review.get("user") or {}).get("login") or (payload.get("sender") or {}).get("login"),
    }


def _normalize_pull_request_review_comment(payload: dict[str, Any]) -> dict[str, Any]:
    comment = payload.get("comment") or {}
    path = comment.get("path")
    path_extension = None
    path_hash = None
    if path:
        path_hash = sha256(path.encode("utf-8")).hexdigest()
        if "." in path.rsplit("/", 1)[-1]:
            path_extension = "." + path.rsplit(".", 1)[-1].lower()

    pr = payload.get("pull_request") or {}
    return {
        "pr_number": payload.get("number") or pr.get("number"),
        "comment_id": comment.get("id"),
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
        "commenter_login": (comment.get("user") or {}).get("login") or (payload.get("sender") or {}).get("login"),
        "path_hash": path_hash,
        "path_extension": path_extension,
    }


def _normalize_workflow_run(payload: dict[str, Any]) -> dict[str, Any]:
    run = payload.get("workflow_run") or {}
    started_at = _parse_dt(run.get("run_started_at"))
    updated_at = _parse_dt(run.get("updated_at"))
    duration_seconds = None
    if started_at and updated_at:
        duration_seconds = max(0, int((updated_at - started_at).total_seconds()))

    return {
        "workflow_id": run.get("workflow_id"),
        "workflow_name": run.get("name"),
        "run_id": run.get("id"),
        "run_number": run.get("run_number"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "run_started_at": run.get("run_started_at"),
        "duration_seconds": duration_seconds,
        "head_branch": run.get("head_branch"),
        "head_sha": run.get("head_sha"),
    }


def _normalize_deployment(payload: dict[str, Any]) -> dict[str, Any]:
    deployment = payload.get("deployment") or {}
    creator = deployment.get("creator") or payload.get("sender") or {}
    return {
        "deployment_id": deployment.get("id"),
        "environment": deployment.get("environment"),
        "state": payload.get("action"),
        "created_at": deployment.get("created_at"),
        "updated_at": deployment.get("updated_at"),
        "creator_login": creator.get("login"),
    }


def _normalize_deployment_status(payload: dict[str, Any]) -> dict[str, Any]:
    deployment = payload.get("deployment") or {}
    status = payload.get("deployment_status") or {}
    creator = status.get("creator") or payload.get("sender") or {}
    return {
        "deployment_id": deployment.get("id") or status.get("deployment_id"),
        "environment": deployment.get("environment"),
        "status": status.get("state"),
        "created_at": status.get("created_at"),
        "updated_at": status.get("updated_at"),
        "creator_login": creator.get("login"),
    }


def normalize_github_event(delivery_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    action = payload.get("action")

    if event_type == "push":
        metadata = _normalize_push(payload)
    elif event_type == "pull_request":
        metadata = _normalize_pull_request(payload)
    elif event_type == "pull_request_review":
        metadata = _normalize_pull_request_review(payload)
    elif event_type == "pull_request_review_comment":
        metadata = _normalize_pull_request_review_comment(payload)
    elif event_type == "workflow_run":
        metadata = _normalize_workflow_run(payload)
    elif event_type == "deployment":
        metadata = _normalize_deployment(payload)
    elif event_type == "deployment_status":
        metadata = _normalize_deployment_status(payload)

    return {
        "id": delivery_id,
        "source": "github",
        "event_type": event_type,
        "action": action,
        "repository": _repository(payload),
        "actor": _actor(payload, event_type),
        "occurred_at": _best_timestamp(event_type, payload),
        "metadata": metadata,
    }
