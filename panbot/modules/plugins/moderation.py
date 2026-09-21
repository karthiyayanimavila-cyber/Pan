from __future__ import annotations

from pyrogram import filters
from pyrogram.types import ChatPermissions

from panbot.registry import register_module
from panbot.runtime import pgram

__mod_name__ = "Moderation"
__help__ = "Reply to a user with /ban, /unban, or /mute in a group."
register_module(__mod_name__, __help__, "plugins")


async def _is_admin(client, message) -> bool:
    if not message.from_user:
        return False
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in {"administrator", "owner"}


async def _target(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1:
        try:
            return int(message.command[1])
        except ValueError:
            return None
    return None


@pgram.on_message(filters.command("ban") & filters.group)
async def ban(client, message):
    if not await _is_admin(client, message):
        return
    target = await _target(message)
    if target:
        await client.ban_chat_member(message.chat.id, target)
        await message.reply_text("User banned.")


@pgram.on_message(filters.command("unban") & filters.group)
async def unban(client, message):
    if not await _is_admin(client, message):
        return
    target = await _target(message)
    if target:
        await client.unban_chat_member(message.chat.id, target)
        await message.reply_text("User unbanned.")


@pgram.on_message(filters.command("mute") & filters.group)
async def mute(client, message):
    if not await _is_admin(client, message):
        return
    target = await _target(message)
    if target:
        await client.restrict_chat_member(message.chat.id, target, ChatPermissions())
        await message.reply_text("User muted.")
