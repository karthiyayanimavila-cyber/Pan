from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def episode_keyboard(episodes: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"episode:{episode_id}")]
            for episode_id, label in episodes
        ]
    )


def quality_keyboard(files: list[object]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(getattr(media, "quality")), callback_data=f"file:{getattr(media, 'id')}")]
            for media in files
        ]
    )
