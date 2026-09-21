from __future__ import annotations

from pyrogram import filters

from panbot.registry import register_module
from panbot.runtime import pgram, settings

__mod_name__ = "Stats"
__help__ = "Show loaded modules and runtime configuration status."
register_module(__mod_name__, __help__, "plugins")


@pgram.on_message(filters.command("stats") & filters.private)
async def stats(_, message):
    from panbot.registry import modules

    await message.reply_text(
        "<b>Pan status</b>\n"
        f"Modules: <code>{len(modules())}</code>\n"
        f"MongoDB: <code>{'configured' if settings.mongo_url else 'disabled'}</code>\n"
        f"Redis: <code>{'configured' if settings.redis_url else 'disabled'}</code>"
    )
