from __future__ import annotations

from aiogram import Bot
from pyrogram import Client

from .config import Settings, load_settings

settings: Settings = load_settings()
settings.workdir.mkdir(parents=True, exist_ok=True)

# Pyrofork owns update delivery and plugin decorators. It is intentionally the
# only Telegram update client in the process.
pgram = Client(
    name="pan",
    api_id=settings.api_id,
    api_hash=settings.api_hash,
    bot_token=settings.bot_token,
    workdir=str(settings.workdir),
)

# aiogram is used only as a typed Bot API 10.3 sender for rich messages. It is
# never started with polling, so there is no competing getUpdates consumer.
bot_api = Bot(settings.bot_token)
