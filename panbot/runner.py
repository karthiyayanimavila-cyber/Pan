from __future__ import annotations

import asyncio
import logging
import os

from pyrogram import idle

from .helper.http import close as close_http
from .loader import load_modules
from .runtime import bot_api, pgram, settings
from .utils.storage import Storage

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("panbot.runner")


async def _heartbeat(path, storage: Storage) -> None:
    while True:
        if pgram.is_connected:
            path.touch()
        await asyncio.sleep(settings.heartbeat_seconds)


async def run() -> None:
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    heartbeat = settings.runtime_dir / "worker.heartbeat"
    storage = Storage(settings)
    loaded, discovered = load_modules()
    log.info("Loaded %s/%s modules", loaded, discovered)
    await storage.start()
    try:
        await pgram.start()
        heartbeat.touch()
        log.info("Pyrofork client started as @%s", (await pgram.get_me()).username)
        task = asyncio.create_task(_heartbeat(heartbeat, storage), name="worker-heartbeat")
        try:
            await idle()
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    finally:
        await storage.close()
        await close_http()
        await pgram.stop()
        await bot_api.session.close()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
