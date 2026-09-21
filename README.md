# Pan Media Library Telegram Bot

A self-hosted Telegram catalog bot for **media you own or are authorized to distribute**. It provides the useful catalog, approval, caching, rich-message, and channel-index patterns found in media bots without scraping random sites or mirroring copyrighted material.

## Stack

- **aiogram 3.31** for the typed Telegram Bot API 10.3 layer
- **Pyrofork** as an optional MTProto companion for an account and allowlisted chats controlled by the operator
- SQLite for the catalog and Telegram `file_id` cache
- A small parent watchdog with a Werkzeug-style `/healthz` keep-alive endpoint
- One custom long-poll loop around aiogram's `Bot.get_updates`, so the watchdog sees a real last-successful-poll heartbeat

Aiogram remains the only Bot API poller. Pyrofork is never started as a second `getUpdates` consumer with the same bot token.

## Features

- Admin-only media intake with `Title | S1E2 | 720p` captions
- 480p, 720p, and 1080p quality buttons
- Search, latest entries, and admin catalog stats
- Cached Telegram file IDs so the bot does not download from external websites
- Rich messages using headings, paragraphs, lists, details sections, and styled callback buttons
- `sendMessageDraft` progress previews with stop/keep-on-stop flags
- Ephemeral error/status responses on callback flows when supported
- Rich channel index messages updated when a new quality is added
- `deleteWebhook`, long-poll timeout, retry backoff, stale heartbeat detection, and process restart
- Optional Pyrofork bridge for authorized MTProto-side integrations

## Responsible-use boundary

Use this only for content you created, licensed, own, or have permission to distribute. This repository does **not** include website scraping, DRM bypassing, cookie theft, arbitrary third-party downloaders, or a copyrighted-content mirror.

## Setup

1. Create a bot with `@BotFather` and copy its token.
2. Get your numeric Telegram user ID with `/id` after starting the bot.
3. Copy `.env.example` to `.env` and set `BOT_TOKEN`, `ADMIN_IDS`, and optionally `TARGET_CHANNEL_ID`.
4. Install and run:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
set -a; . ./.env; set +a
python -m panbot
```

The health endpoint listens on `0.0.0.0:$PORT`. The parent supervisor starts one worker. If that worker exits or its last successful `getUpdates` call becomes older than `POLL_STALE_SECONDS`, it is terminated and restarted with backoff. Do not run another copy with the same bot token.

## Add media

In a private chat with the bot, an admin uploads a video or document with a caption such as:

```text
My Authorized Series | S1E2 | 720p
```

Allowed quality labels are `480p`, `720p`, and `1080p`. Uploading the same episode and quality updates its cached Telegram file ID. If `TARGET_CHANNEL_ID` is configured, Pan keeps a rich channel index post updated with quality buttons.

## Optional Pyrofork bridge

The bridge is disabled by default. To enable it, set `ENABLE_PYROFORK=true`, `PYRO_API_ID`, `PYRO_API_HASH`, and an allowlist in `PYRO_SOURCE_CHAT_IDS`. Use an account and source chats you control or are authorized to use. On first start, Pyrofork may require an interactive login, so use a persistent server volume for its session file.

This integration is intentionally not a web scraper or an arbitrary channel copier.

## Docker

```bash
cp .env.example .env
# edit .env
docker build -t panbot .
docker run --env-file .env -p 8080:8080 -v "$PWD/data:/app/data" -v "$PWD/.runtime:/app/.runtime" panbot
```

## Telegram API 10.3 notes

The code uses the current aiogram 3.31 types and methods for rich messages, rich drafts, ephemeral message parameters, and the `message_generation_stopped` update. Rich messages are finalized with `sendRichMessage`; drafts are temporary previews and are not used as the persisted catalog response.

References:

- [Telegram Bot API changelog](https://core.telegram.org/bots/api-changelog)
- [Telegram Bot API rich messages](https://core.telegram.org/bots/api#richmessages)
- [Telegram getUpdates](https://core.telegram.org/bots/api#getupdates)
- [aiogram sendRichMessage](https://docs.aiogram.dev/en/latest/api/methods/send_rich_message.html)
- [Pyrofork](https://github.com/Mayuri-Chan/pyrofork)
