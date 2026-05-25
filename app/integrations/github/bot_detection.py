def is_bot_actor(actor_login: str | None, actor_type: str | None) -> bool:
    login = (actor_login or "").strip().lower()
    normalized_type = (actor_type or "").strip().lower()

    if normalized_type == "bot":
        return True
    if login in {"dependabot", "renovate", "github-actions[bot]"}:
        return True
    return login.endswith("[bot]")
