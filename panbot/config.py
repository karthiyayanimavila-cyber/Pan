from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing."""


def _int_set(value: str) -> frozenset[int]:
    values: set[int] = set()
    for raw in value.split(","):
        raw = raw.strip()
        if raw:
            try:
                values.add(int(raw))
            except ValueError as exc:
                raise ConfigError(f"Invalid numeric Telegram ID: {raw!r}") from exc
    return frozenset(values)


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    bot_token: str
    owner_ids: frozenset[int]
    mongo_url: str | None
    mongo_db: str
    redis_url: str | None
    support_chat: str
    update_channel: str
    start_image: str | None
    bot_name: str
    workdir: Path
    runtime_dir: Path
    port: int
    heartbeat_seconds: int
    poll_stale_seconds: int
    restart_backoff_seconds: int
    log_level: str

    def is_owner(self, user_id: int) -> bool:
        return user_id in self.owner_ids


def load_settings() -> Settings:
    missing: list[str] = []
    api_id = os.getenv("API_ID", "").strip()
    api_hash = os.getenv("API_HASH", "").strip()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not api_id:
        missing.append("API_ID")
    if not api_hash:
        missing.append("API_HASH")
    if not bot_token:
        missing.append("BOT_TOKEN")
    if missing:
        raise ConfigError("Missing required environment variables: " + ", ".join(missing))

    owner_ids = _int_set(os.getenv("OWNER_IDS", os.getenv("ADMIN_IDS", "")))
    if not owner_ids:
        raise ConfigError("OWNER_IDS must contain at least one numeric Telegram user ID")

    return Settings(
        api_id=int(api_id),
        api_hash=api_hash,
        bot_token=bot_token,
        owner_ids=owner_ids,
        mongo_url=os.getenv("MONGO_URL", "").strip() or None,
        mongo_db=os.getenv("MONGO_DB", "pan"),
        redis_url=os.getenv("REDIS_URL", "").strip() or None,
        support_chat=os.getenv("SUPPORT_CHAT", "").strip(),
        update_channel=os.getenv("UPDATE_CHANNEL", "").strip(),
        start_image=os.getenv("START_IMAGE", "").strip() or None,
        bot_name=os.getenv("BOT_NAME", "Pan"),
        workdir=Path(os.getenv("WORKDIR", "data/sessions")),
        runtime_dir=Path(os.getenv("RUNTIME_DIR", ".runtime")),
        port=max(1, int(os.getenv("PORT", "8080"))),
        heartbeat_seconds=max(5, int(os.getenv("HEARTBEAT_SECONDS", "15"))),
        poll_stale_seconds=max(30, int(os.getenv("POLL_STALE_SECONDS", "90"))),
        restart_backoff_seconds=max(1, int(os.getenv("RESTART_BACKOFF_SECONDS", "5"))),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
