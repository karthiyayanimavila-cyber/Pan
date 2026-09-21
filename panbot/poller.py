from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import load_settings
from .db import Database
from .handlers import BotHandlers, build_router
from .mtproto import AuthorizedMTProtoBridge

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("panbot.poller")


async def run() -> None:
    settings = load_settings()
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    heartbeat = settings.runtime_dir / "poller.heartbeat"
    db = Database(settings.db_path)
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    handlers = BotHandlers(bot, db, settings)
    dispatcher.include_router(build_router(handlers))
    mtproto = AuthorizedMTProtoBridge(settings)
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        me = await bot.get_me()
        log.info("Aiogram Bot API 10.3 poller active as @%s", me.username or me.id)
        await mtproto.start()

        # We use aiogram's typed Bot and Dispatcher, but own the getUpdates loop so
        # the supervisor heartbeat is updated after each successful long poll.
        offset: int | None = None
        while True:
            updates = await bot.get_updates(
                offset=offset,
                limit=100,
                timeout=settings.poll_timeout,
                allowed_updates=["message", "callback_query", "stopped_message_generation"],
            )
            heartbeat.touch()
            for update in updates:
                offset = update.update_id + 1
                try:
                    await dispatcher.feed_update(bot, update)
                except Exception:
                    log.exception("Update %s failed", update.update_id)
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception("Polling stopped; supervisor will restart this worker")
        raise
    finally:
        await mtproto.stop()
        await bot.session.close()
        db.close()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
