from __future__ import annotations

import asyncio
import logging

log = logging.getLogger("panbot.tasks")
_tasks: set[asyncio.Task] = set()


def spawn(coro, name: str) -> asyncio.Task:
    task = asyncio.create_task(coro, name=name)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    task.add_done_callback(_log_failure)
    return task


def _log_failure(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        log.error("Background task %s failed", task.get_name(), exc_info=task.exception())
