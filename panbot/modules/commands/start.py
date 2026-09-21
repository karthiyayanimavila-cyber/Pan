from __future__ import annotations

from pyrogram import filters

from panbot.helper.rich import buttons, details, heading, paragraph, send_rich, bullet_list
from panbot.registry import register_module
from panbot.runtime import pgram, settings

__mod_name__ = "Start"
__help__ = "Welcome message and quick actions."
register_module(__mod_name__, __help__, "commands")


@pgram.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user = message.from_user.first_name if message.from_user else "there"
    rich = __import__("aiogram.types", fromlist=["InputRichMessage"]).InputRichMessage(
        blocks=[
            heading(f"✨ {settings.bot_name}", 1),
            paragraph(f"Hello {user}! I am a modular Telegram assistant inspired by Emilia."),
            details(
                "Available now",
                [bullet_list(["Group moderation", "Anime information", "Rich help menus", "Plugin-based expansion"])],
                is_open=True,
            ),
            buttons([("Help", "primary", "help:main"), ("Anime", "success", "anime:help")]),
        ]
    )
    await send_rich(message.chat.id, rich)
