from __future__ import annotations

from collections.abc import Iterable

from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockDetails,
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichMessage,
    RichMessageButton,
)

from .db import Episode, MediaFile


def episode_label(episode: Episode) -> str:
    return f"{episode.title} — S{episode.season:02d}E{episode.episode:02d}"


def _quality_buttons(files: Iterable[MediaFile]) -> list[RichMessageButton]:
    return [
        RichMessageButton(text=f"{media.quality} 📥", style="success", callback_data=f"file:{media.id}")
        for media in files
    ]


def episode_message(episode: Episode, files: list[MediaFile]) -> InputRichMessage:
    qualities = InputRichBlockList(
        items=[
            InputRichBlockListItem(
                blocks=[InputRichBlockParagraph(text=f"{media.quality} available")]
            )
            for media in files
        ]
    )
    blocks = [
        InputRichBlockSectionHeading(text=episode_label(episode), size=2),
        InputRichBlockParagraph(text="Choose an authorized media quality below."),
        InputRichBlockDetails(summary="Available qualities", blocks=[qualities], is_open=True),
        InputRichBlockButtons(buttons=_quality_buttons(files)),
    ]
    return InputRichMessage(blocks=blocks)


def search_message(heading: str, episodes: list[Episode]) -> InputRichMessage:
    items = InputRichBlockList(
        items=[
            InputRichBlockListItem(
                blocks=[InputRichBlockParagraph(text=episode_label(episode))]
            )
            for episode in episodes
        ]
    )
    buttons = InputRichBlockButtons(
        buttons=[
            RichMessageButton(text=f"Open {index}", style="primary", callback_data=f"episode:{episode.id}")
            for index, episode in enumerate(episodes, start=1)
        ]
    )
    return InputRichMessage(
        blocks=[
            InputRichBlockSectionHeading(text=heading, size=2),
            items,
            buttons,
        ]
    )
