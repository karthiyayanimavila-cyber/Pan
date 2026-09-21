from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from ..config import Settings

log = logging.getLogger("panbot.storage")


class Storage:
    """Optional MongoDB/Redis storage in the same spirit as Emilia.

    The bot still boots without either service, which makes local development
    simple. Production deployments can enable both through environment vars.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.mongo = None
        self.db = None
        self.redis = None

    async def start(self) -> None:
        if self.settings.mongo_url:
            from motor.motor_asyncio import AsyncIOMotorClient

            self.mongo = AsyncIOMotorClient(self.settings.mongo_url, serverSelectionTimeoutMS=3000)
            self.db = self.mongo[self.settings.mongo_db]
            try:
                await self.mongo.admin.command("ping")
                log.info("MongoDB connected: %s", self.settings.mongo_db)
            except Exception:
                log.exception("MongoDB is configured but not reachable")
        if self.settings.redis_url:
            from redis.asyncio import Redis

            self.redis = Redis.from_url(self.settings.redis_url, decode_responses=True)
            try:
                await self.redis.ping()
                log.info("Redis connected")
            except Exception:
                log.exception("Redis is configured but not reachable")

    async def record_command(self, command: str, user_id: int | None = None) -> None:
        if self.redis is not None:
            try:
                await self.redis.hincrby("pan:metrics:commands", command, 1)
            except Exception:
                log.debug("Could not record Redis metric", exc_info=True)
        if self.db is not None:
            try:
                await self.db.command_events.insert_one(
                    {"command": command, "user_id": user_id, "at": datetime.now(timezone.utc)}
                )
            except Exception:
                log.debug("Could not record Mongo command event", exc_info=True)

    async def stats(self) -> dict[str, Any]:
        result: dict[str, Any] = {"mongo": self.db is not None, "redis": self.redis is not None}
        if self.redis is not None:
            try:
                result["commands"] = await self.redis.hgetall("pan:metrics:commands")
            except Exception:
                result["commands"] = {}
        return result

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()
        if self.mongo is not None:
            self.mongo.close()
