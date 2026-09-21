from __future__ import annotations

import html
import re
import time
from typing import Any

from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.methods import (
    EditMessageText,
    SendRichMessage,
    SendRichMessageDraft,
)
from aiogram.types import (
    CallbackQuery,
    EphemeralMessageParameters,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageGenerationStopped,
    InputRichBlockThinking,
    InputRichMessage,
)

from .config import Settings
from .db import Database, Episode
from .keyboards import episode_keyboard, quality_keyboard
from .rich import episode_label, episode_message, search_message

CAPTION_RE = re.compile(
    r"^\s*(?P<title>[^|]+?)\s*\|\s*(?:S(?P<season>\d+)\s*)?E?(?P<episode>\d+)\s*\|\s*(?P<quality>480p|720p|1080p)\s*$",
    re.IGNORECASE,
)


class BotHandlers:
    def __init__(self, bot: Bot, db: Database, settings: Settings):
        self.bot = bot
        self.db = db
        self.settings = settings

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.settings.admin_ids

    async def send_rich(self, chat_id: int | str, rich: InputRichMessage, **extra: Any) -> Message:
        return await self.bot(SendRichMessage(chat_id=chat_id, rich_message=rich, **extra))

    async def send_ephemeral_error(self, callback: CallbackQuery, text: str) -> None:
        if not callback.from_user:
            return
        try:
            await self.bot.send_message(
                callback.from_user.id,
                text,
                ephemeral_message_parameters=EphemeralMessageParameters(
                    receiver_user_id=callback.from_user.id,
                    callback_query_id=callback.id,
                    replace_callback_query_message=True,
                ),
            )
        except TelegramAPIError:
            await callback.answer(text, show_alert=True)

    async def draft(self, message: Message, text: str) -> None:
        if not self.settings.use_drafts or message.chat.type != "private" or not message.from_user:
            return
        try:
            await self.bot(
                SendRichMessageDraft(
                    chat_id=message.chat.id,
                    draft_id=int(time.time() * 1000) % 2_000_000_000,
                    rich_message=InputRichMessage(
                        blocks=[InputRichBlockThinking(text=text)]
                    ),
                    can_stop=True,
                    keep_on_stop=True,
                )
            )
        except TelegramAPIError:
            return

    async def show_results(self, message: Message, heading: str, episodes: list[Episode]) -> None:
        if not episodes:
            await message.answer(
                "No matching authorized entries yet.\n\nAdmin upload caption format:\n<code>Title | S1E1 | 720p</code>"
            )
            return
        try:
            await self.send_rich(message.chat.id, search_message(heading, episodes), protect_content=True)
        except TelegramAPIError:
            await message.answer(
                f"<b>{html.escape(heading)}</b>\n\n" + "\n".join(
                    f"• {html.escape(episode_label(episode))}" for episode in episodes
                ),
                reply_markup=episode_keyboard([(episode.id, "Open") for episode in episodes]),
            )

    async def publish_episode(self, episode: Episode) -> None:
        channel = self.settings.target_channel_id
        files = self.db.files_for_episode(episode.id)
        if not channel or not files:
            return
        rich = episode_message(episode, files)
        existing = self.db.channel_post(episode.id)
        if existing:
            try:
                await self.bot(
                    EditMessageText(
                        chat_id=existing[0],
                        message_id=existing[1],
                        rich_message=rich,
                    )
                )
                return
            except TelegramBadRequest as exc:
                if "not modified" in str(exc).lower():
                    return
        try:
            result = await self.bot(
                SendRichMessage(
                    chat_id=channel,
                    rich_message=rich,
                    protect_content=True,
                )
            )
        except TelegramAPIError:
            result = await self.bot.send_message(
                channel,
                f"<b>{html.escape(episode_label(episode))}</b>\nChoose a quality:",
                reply_markup=quality_keyboard(files),
                protect_content=True,
            )
        self.db.save_channel_post(episode.id, str(channel), result.message_id)

    async def handle_media(self, message: Message) -> None:
        if not message.from_user or not self.is_admin(message.from_user.id):
            await message.answer("Only an authorized admin can add catalog media.")
            return
        parsed = CAPTION_RE.match(message.caption or "")
        if not parsed:
            await message.answer(
                "Use this caption format:\n<code>Title | S1E2 | 720p</code>\n\nAllowed: 480p, 720p, 1080p"
            )
            return
        title = parsed.group("title").strip()
        season = int(parsed.group("season") or 1)
        episode_number = int(parsed.group("episode"))
        quality = parsed.group("quality").lower()
        if message.video:
            media_type, file_id = "video", message.video.file_id
        elif message.document:
            media_type, file_id = "document", message.document.file_id
        else:
            return
        episode = self.db.upsert_episode(title, season, episode_number)
        self.db.upsert_file(episode.id, quality, media_type, file_id, message.chat.id, message.message_id)
        await message.answer(f"Saved <b>{html.escape(episode_label(episode))}</b> at <b>{quality}</b>.")
        try:
            await self.publish_episode(episode)
        except TelegramAPIError as exc:
            await message.answer(f"Saved locally, but channel publishing failed: <code>{html.escape(str(exc))}</code>")

    async def callback(self, callback: CallbackQuery) -> None:
        data = callback.data or ""
        await callback.answer()
        if data.startswith("episode:"):
            episode = self.db.get_episode(int(data.split(":", 1)[1]))
            if not episode or not callback.from_user:
                return
            files = self.db.files_for_episode(episode.id)
            if not files:
                await self.send_ephemeral_error(callback, "No quality files are available.")
                return
            try:
                await self.send_rich(callback.from_user.id, episode_message(episode, files), protect_content=True)
            except TelegramAPIError:
                await callback.message.answer("Choose a quality:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f.quality, callback_data=f"file:{f.id}") for f in files]
                ])) if callback.message else None
        elif data.startswith("file:"):
            media = self.db.get_file(int(data.split(":", 1)[1]))
            if not media or not callback.from_user:
                return
            try:
                if media.media_type == "video":
                    await self.bot.send_video(callback.from_user.id, media.telegram_file_id, protect_content=True)
                else:
                    await self.bot.send_document(callback.from_user.id, media.telegram_file_id, protect_content=True)
            except TelegramAPIError:
                await self.send_ephemeral_error(callback, "Open the bot and send /start before requesting a file.")


def build_router(handlers: BotHandlers) -> Router:
    router = Router(name="panbot")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(
            "<b>Pan Media Library</b>\n\nSearch an authorized catalog with /search or /latest.\n\nThis bot accepts only media you own or are licensed to distribute."
        )

    @router.message(Command("help", "about"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "<b>Commands</b>\n/search &lt;title&gt; — search\n/latest — newest entries\n/id — your Telegram ID\n/stats — admin catalog stats\n\nAdmin upload: <code>Title | S1E2 | 720p</code>"
        )

    @router.message(Command("id"))
    async def id_command(message: Message) -> None:
        await message.answer(f"Your Telegram ID is <code>{message.from_user.id if message.from_user else 'unknown'}</code>")

    @router.message(Command("search"))
    async def search_command(message: Message, command: CommandObject) -> None:
        query = (command.args or "").strip()
        if not query:
            await message.answer("Usage: /search &lt;title&gt;")
            return
        await handlers.draft(message, f"Searching for “{html.escape(query)}”…")
        await handlers.show_results(message, f"Search: {query}", handlers.db.search(query))

    @router.message(Command("latest"))
    async def latest_command(message: Message) -> None:
        await handlers.show_results(message, "Latest catalog entries", handlers.db.latest())

    @router.message(Command("stats"))
    async def stats_command(message: Message) -> None:
        if not message.from_user or not handlers.is_admin(message.from_user.id):
            await message.answer("Admin only.")
            return
        episodes, files = handlers.db.counts()
        await message.answer(f"Catalog: <b>{episodes}</b> episodes, <b>{files}</b> quality files.")

    @router.message(F.video | F.document)
    async def media_message(message: Message) -> None:
        await handlers.handle_media(message)

    @router.callback_query()
    async def callback_query(callback: CallbackQuery) -> None:
        await handlers.callback(callback)

    @router.stopped_message_generation()
    async def stopped_generation(event: MessageGenerationStopped) -> None:
        await handlers.bot.send_message(event.chat.id, "Okay, stopped.")

    @router.message()
    async def fallback(message: Message) -> None:
        await message.answer("I did not understand that. Try /help.")

    return router
