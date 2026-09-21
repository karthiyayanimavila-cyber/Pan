from __future__ import annotations

import time

from pyrogram import filters

from panbot.registry import register_module
from panbot.runtime import pgram, settings

__mod_name__ = "Ping"
__help__ = "Check bot responsiveness and show your Telegram ID."
register_module(__mod_name__, __help__, "commands")
_started = time.monotonic()


@pgram.on_message(filters.command(["ping", "id"]))
async def ping(_, message):
    if message.command[0].lower() == "id":
        await message.reply_text(f"Your Telegram ID: <code>{message.from_user.id if message.from_user else 'unknown'}</code>")
        return
    uptime = int(time.monotonic() - _started)
    await message.reply_text(f"🏓 <b>Pong</b>\nUptime: <code>{uptime}s</code>\nBot: <code>{settings.bot_name}</code>")
