from __future__ import annotations

import logging

from .config import Settings

log = logging.getLogger("panbot.mtproto")


class AuthorizedMTProtoBridge:
    """Optional Pyrofork companion for an account the operator controls.

    Aiogram remains the only Bot API polling client. This bridge is disabled by
    default and is deliberately limited to an allowlist of source chats. It is
    useful for approved internal channels, not for scraping random websites or
    copying material without permission.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None

    async def start(self) -> None:
        if not self.settings.enable_pyrofork:
            return
        if not self.settings.pyro_source_chat_ids:
            log.warning("Pyrofork enabled but PYRO_SOURCE_CHAT_IDS is empty; bridge will only report status")
        from pyrogram import Client

        self.client = Client(
            self.settings.pyro_session_name,
            api_id=self.settings.pyro_api_id,
            api_hash=self.settings.pyro_api_hash,
        )
        await self.client.start()
        me = await self.client.get_me()
        log.info("Pyrofork MTProto session active as %s", getattr(me, "username", None) or me.id)

    async def stop(self) -> None:
        if self.client is not None:
            await self.client.stop()
            self.client = None
