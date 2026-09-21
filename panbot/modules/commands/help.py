from __future__ import annotations

from pyrogram import filters

from panbot.helper.rich import bullet_list, buttons, heading, paragraph, send_rich
from panbot.registry import modules, register_module
from panbot.runtime import pgram

__mod_name__ = "Help"
__help__ = "Browse the auto-loaded module list."
register_module(__mod_name__, __help__, "commands")


def _message():
    from aiogram.types import InputRichMessage

    entries = modules()
    return InputRichMessage(
        blocks=[
            heading("📚 Pan Help", 1),
            paragraph("Modules are discovered automatically from panbot/modules."),
            bullet_list([f"{item.name}: {item.help_text}" for item in entries]),
            buttons([("Start", "primary", "help:start"), ("Refresh", "success", "help:main")]),
        ]
    )


@pgram.on_message(filters.command(["help", "modules"]))
async def help_command(_, message):
    await send_rich(message.chat.id, _message())


@pgram.on_callback_query(filters.regex(r"^help:(main|start)$"))
async def help_callback(_, query):
    await query.answer()
    if query.from_user:
        await send_rich(query.from_user.id, _message())
