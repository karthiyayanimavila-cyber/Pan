from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendRichMessage
from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockDetails,
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichMessage,
    InlineKeyboardMarkup,
    RichMessageButton,
)

from ..runtime import bot_api


def heading(text: str, size: int = 2) -> InputRichBlockSectionHeading:
    return InputRichBlockSectionHeading(text=text, size=size)


def paragraph(text: str) -> InputRichBlockParagraph:
    return InputRichBlockParagraph(text=text)


def bullet_list(items: Iterable[str]) -> InputRichBlockList:
    return InputRichBlockList(
        items=[
            InputRichBlockListItem(blocks=[InputRichBlockParagraph(text=item)])
            for item in items
        ]
    )


def buttons(buttons: Iterable[tuple[str, str, str | None]]) -> InputRichBlockButtons:
    return InputRichBlockButtons(
        buttons=[
            RichMessageButton(text=text, style=style, callback_data=callback_data)
            for text, style, callback_data in buttons
        ]
    )


def details(summary: str, blocks: list[Any], is_open: bool = False) -> InputRichBlockDetails:
    return InputRichBlockDetails(summary=summary, blocks=blocks, is_open=is_open)


async def send_rich(
    chat_id: int | str,
    message: InputRichMessage,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    protect_content: bool = False,
) -> Any:
    """Send a Bot API 10.3 rich message, with a plain fallback."""
    try:
        return await bot_api(
            SendRichMessage(
                chat_id=chat_id,
                rich_message=message,
                reply_markup=reply_markup,
                protect_content=protect_content,
            )
        )
    except TelegramAPIError:
        # The user still receives something if the chat/client cannot accept a
        # rich message yet. The caller can continue using the same module API.
        text = "\n".join(_plain_text(message))
        return await bot_api.send_message(chat_id, text, reply_markup=reply_markup)


def _plain_text(message: InputRichMessage) -> list[str]:
    lines: list[str] = []
    for block in message.blocks or []:
        data = block.model_dump(exclude_none=True)
        for key in ("text", "summary"):
            if data.get(key):
                lines.append(str(data[key]))
    return lines or ["Pan"]
