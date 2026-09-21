from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    pass


def _int_set(value: str) -> frozenset[int]:
    result: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if item:
            try:
                result.add(int(item))
            except ValueError as exc:
                raise ConfigError(f"Invalid numeric ID: {item!r}") from exc
    return frozenset(result)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    target_channel_id: str | None
    db_path: Path
    runtime_dir: Path
    port: int
    poll_timeout: int
    poll_stale_seconds: int
    restart_backoff_seconds: int
    use_drafts: bool
    enable_pyrofork: bool
    pyro_api_id: int | None
    pyro_api_hash: str | None
    pyro_session_name: str
    pyro_source_chat_ids: frozenset[int]


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError("BOT_TOKEN is required")
    admin_ids = _int_set(os.getenv("ADMIN_IDS", ""))
    if not admin_ids:
        raise ConfigError("ADMIN_IDS must contain at least one numeric Telegram user ID")

    api_id = os.getenv("PYRO_API_ID", "").strip()
    api_hash = os.getenv("PYRO_API_HASH", "").strip()
    enable_pyrofork = os.getenv("ENABLE_PYROFORK", "false").lower() in {"1", "true", "yes", "on"}
    if enable_pyrofork and (not api_id or not api_hash):
        raise ConfigError("ENABLE_PYROFORK=true requires PYRO_API_ID and PYRO_API_HASH")

    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        target_channel_id=os.getenv("TARGET_CHANNEL_ID", "").strip() or None,
        db_path=Path(os.getenv("DB_PATH", "data/panbot.sqlite3")),
        runtime_dir=Path(os.getenv("RUNTIME_DIR", ".runtime")),
        port=max(1, int(os.getenv("PORT", "8080"))),
        poll_timeout=max(1, int(os.getenv("POLL_TIMEOUT", "30"))),
        poll_stale_seconds=max(30, int(os.getenv("POLL_STALE_SECONDS", "90"))),
        restart_backoff_seconds=max(1, int(os.getenv("RESTART_BACKOFF_SECONDS", "5"))),
        use_drafts=os.getenv("USE_DRAFTS", "true").lower() in {"1", "true", "yes", "on"},
        enable_pyrofork=enable_pyrofork,
        pyro_api_id=int(api_id) if api_id else None,
        pyro_api_hash=api_hash or None,
        pyro_session_name=os.getenv("PYRO_SESSION_NAME", "pan_mtproto"),
        pyro_source_chat_ids=_int_set(os.getenv("PYRO_SOURCE_CHAT_IDS", "")),
    )
