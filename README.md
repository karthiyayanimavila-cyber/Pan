# Pan

A modular, multipurpose Telegram bot built in the style of the Emilia project: auto-loaded command modules, plugin modules, a Pyrogram-compatible MTProto client, optional MongoDB/Redis services, rich help menus, and a restart-aware worker.

This is an original implementation inspired by the **architecture and UX patterns** of Emilia, not a copy of its source. Emilia describes itself as a multipurpose Telegram bot with anime, AI, and group-management features [Emilia](https://github.com/ArshCypherZ/Emilia).

## What is included

- Pyrofork client for update delivery and plugin decorators
- aiogram 3.31 as a **non-polling** Bot API 10.3 sender for rich messages
- Automatic module discovery from `panbot/modules/`
- `/start`, `/help`, `/modules`, `/ping`, `/id`, and `/stats`
- Anime search and details through the public Jikan metadata API
- `/ban`, `/unban`, and `/mute` for group administrators
- Rich headings, lists, details blocks, and styled callback buttons
- Optional MongoDB event storage
- Optional Redis command metrics
- `0.0.0.0:$PORT/healthz` keep-alive endpoint
- Supervisor that restarts the worker when its heartbeat becomes stale

The bot deliberately uses only one Telegram update consumer. Pyrofork handles updates; aiogram only sends Bot API rich messages. Running two polling clients with one token would cause conflicts.

## Responsible use

This bot is designed for moderation, anime metadata, community utilities, and content you own or are authorized to distribute. It does not include a scraper, DRM bypass, arbitrary third-party downloader, or copyrighted-content mirror.

## Setup

```bash
cp .env.example .env
# edit API_ID, API_HASH, BOT_TOKEN, and OWNER_IDS

python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
set -a; . ./.env; set +a
python -m panbot
```

Create `API_ID` and `API_HASH` at [my.telegram.org](https://my.telegram.org), and create `BOT_TOKEN` with `@BotFather`. `OWNER_IDS` is a comma-separated list of numeric Telegram user IDs.

## Add a module

Create a file below `panbot/modules/commands/` or `panbot/modules/plugins/`:

```python
from pyrogram import filters
from panbot.registry import register_module
from panbot.runtime import pgram

__mod_name__ = "Example"
__help__ = "A small example command."
register_module(__mod_name__, __help__, "plugins")


@pgram.on_message(filters.command("example"))
async def example(_, message):
    await message.reply_text("Example works!")
```

The loader imports every Python module at startup and `/help` reads the registry automatically.

## Optional services

Set `MONGO_URL` and/or `REDIS_URL` in `.env` for production persistence and metrics. The bot can still start without them for local development.

## Bot API 10.3 rich messages

The official Bot API 10.3 changelog includes rich messages and ephemeral-message features [Telegram changelog](https://core.telegram.org/bots/api-changelog). This project uses aiogram's typed rich-message methods [aiogram `sendRichMessage`](https://docs.aiogram.dev/en/latest/api/methods/send_rich_message.html), while Pyrofork provides the MTProto-side client [Pyrofork](https://github.com/Mayuri-Chan/pyrofork).

## Docker

```bash
cp .env.example .env
# edit .env
docker build -t pan .
docker run --env-file .env -p 8080:8080 \
  -v "$PWD/data:/app/data" \
  -v "$PWD/.runtime:/app/.runtime" pan
```
