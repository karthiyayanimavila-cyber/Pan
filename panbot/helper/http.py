from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

_session: aiohttp.ClientSession | None = None
_lock = asyncio.Lock()


async def session() -> aiohttp.ClientSession:
    global _session
    async with _lock:
        if _session is None or _session.closed:
            _session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=20),
                headers={"User-Agent": "PanBot/0.1"},
            )
        return _session


async def get_json(url: str, **params: Any) -> Any:
    client = await session()
    async with client.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()


async def close() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()
    _session = None
