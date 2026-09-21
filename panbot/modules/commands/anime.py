from __future__ import annotations

import html

from pyrogram import filters

from panbot.helper.http import get_json
from panbot.helper.rich import bullet_list, buttons, details, heading, paragraph, send_rich
from panbot.registry import register_module
from panbot.runtime import pgram

__mod_name__ = "Anime"
__help__ = "Search public anime metadata with /anime <title>."
register_module(__mod_name__, __help__, "commands")


async def _search(query: str):
    data = await get_json("https://api.jikan.moe/v4/anime", q=query, limit=5)
    return data.get("data", [])


@pgram.on_message(filters.command("anime"))
async def anime_search(_, message):
    query = " ".join(message.command[1:]).strip()
    if not query:
        await message.reply_text("Usage: <code>/anime one piece</code>")
        return
    try:
        results = await _search(query)
    except Exception:
        await message.reply_text("Anime search is temporarily unavailable. Try again shortly.")
        return
    if not results:
        await message.reply_text("No anime found.")
        return
    from aiogram.types import InputRichMessage

    labels = [f"{item.get('title', 'Unknown')} ({item.get('year') or '—'})" for item in results]
    rich = InputRichMessage(
        blocks=[
            heading(f"🔎 Anime: {html.escape(query)}", 2),
            paragraph("Select a result to view public metadata."),
            bullet_list(labels),
            buttons([
                (str(index), "primary", f"anime:{item.get('mal_id')}")
                for index, item in enumerate(results, start=1)
            ]),
        ]
    )
    await send_rich(message.chat.id, rich)


@pgram.on_callback_query(filters.regex(r"^anime:help$"))
async def anime_help(_, query):
    await query.answer("Use /anime <title>", show_alert=True)


@pgram.on_callback_query(filters.regex(r"^anime:(\d+)$"))
async def anime_detail(_, query):
    await query.answer()
    mal_id = query.matches[0].group(1)
    try:
        item = (await get_json(f"https://api.jikan.moe/v4/anime/{mal_id}/full")).get("data", {})
    except Exception:
        if query.from_user:
            await pgram.send_message(query.from_user.id, "Anime details are temporarily unavailable.")
        return
    title = html.escape(str(item.get("title") or "Unknown"))
    synopsis = html.escape(str(item.get("synopsis") or "No synopsis available."))
    genres = ", ".join(str(entry.get("name")) for entry in item.get("genres", [])) or "—"
    from aiogram.types import InputRichMessage

    rich = InputRichMessage(
        blocks=[
            heading(title, 2),
            paragraph(f"Score: {item.get('score') or '—'} | Episodes: {item.get('episodes') or '—'}"),
            details("Genres", [paragraph(html.escape(genres))], is_open=True),
            details("Synopsis", [paragraph(synopsis[:1200])], is_open=False),
            buttons([("Back to search", "primary", "help:main")]),
        ]
    )
    if query.from_user:
        await send_rich(query.from_user.id, rich)
