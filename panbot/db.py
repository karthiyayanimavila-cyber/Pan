from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Episode:
    id: int
    title: str
    season: int
    episode: int
    created_at: str


@dataclass(frozen=True)
class MediaFile:
    id: int
    episode_id: int
    quality: str
    media_type: str
    telegram_file_id: str
    source_chat_id: int
    source_message_id: int
    created_at: str


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    season INTEGER NOT NULL DEFAULT 1,
                    episode INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(title COLLATE NOCASE, season, episode)
                );
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_id INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
                    quality TEXT NOT NULL CHECK(quality IN ('480p', '720p', '1080p')),
                    media_type TEXT NOT NULL CHECK(media_type IN ('video', 'document')),
                    telegram_file_id TEXT NOT NULL,
                    source_chat_id INTEGER NOT NULL,
                    source_message_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(episode_id, quality)
                );
                CREATE TABLE IF NOT EXISTS channel_posts (
                    episode_id INTEGER PRIMARY KEY REFERENCES episodes(id) ON DELETE CASCADE,
                    chat_id TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    @staticmethod
    def _episode(row: sqlite3.Row | None) -> Episode | None:
        if row is None:
            return None
        return Episode(row["id"], row["title"], row["season"], row["episode"], row["created_at"])

    @staticmethod
    def _file(row: sqlite3.Row | None) -> MediaFile | None:
        if row is None:
            return None
        return MediaFile(
            row["id"], row["episode_id"], row["quality"], row["media_type"],
            row["telegram_file_id"], row["source_chat_id"], row["source_message_id"], row["created_at"],
        )

    def upsert_episode(self, title: str, season: int, episode: int) -> Episode:
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO episodes(title, season, episode) VALUES (?, ?, ?)",
                (title.strip(), season, episode),
            )
            row = self._connection.execute(
                "SELECT * FROM episodes WHERE title = ? COLLATE NOCASE AND season = ? AND episode = ?",
                (title.strip(), season, episode),
            ).fetchone()
        result = self._episode(row)
        assert result is not None
        return result

    def upsert_file(
        self,
        episode_id: int,
        quality: str,
        media_type: str,
        telegram_file_id: str,
        source_chat_id: int,
        source_message_id: int,
    ) -> MediaFile:
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO media_files
                   (episode_id, quality, media_type, telegram_file_id, source_chat_id, source_message_id)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(episode_id, quality) DO UPDATE SET
                     media_type = excluded.media_type,
                     telegram_file_id = excluded.telegram_file_id,
                     source_chat_id = excluded.source_chat_id,
                     source_message_id = excluded.source_message_id,
                     created_at = CURRENT_TIMESTAMP""",
                (episode_id, quality, media_type, telegram_file_id, source_chat_id, source_message_id),
            )
            row = self._connection.execute(
                "SELECT * FROM media_files WHERE episode_id = ? AND quality = ?",
                (episode_id, quality),
            ).fetchone()
        result = self._file(row)
        assert result is not None
        return result

    def search(self, query: str, limit: int = 10) -> list[Episode]:
        with self._lock:
            rows = self._connection.execute(
                """SELECT * FROM episodes WHERE title LIKE ? COLLATE NOCASE
                   ORDER BY title COLLATE NOCASE, season, episode LIMIT ?""",
                (f"%{query.strip()}%", limit),
            ).fetchall()
        return [self._episode(row) for row in rows if row is not None]

    def latest(self, limit: int = 10) -> list[Episode]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM episodes ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._episode(row) for row in rows if row is not None]

    def get_episode(self, episode_id: int) -> Episode | None:
        with self._lock:
            row = self._connection.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,)).fetchone()
        return self._episode(row)

    def get_file(self, file_id: int) -> MediaFile | None:
        with self._lock:
            row = self._connection.execute("SELECT * FROM media_files WHERE id = ?", (file_id,)).fetchone()
        return self._file(row)

    def files_for_episode(self, episode_id: int) -> list[MediaFile]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM media_files WHERE episode_id = ? ORDER BY CASE quality WHEN '480p' THEN 1 WHEN '720p' THEN 2 ELSE 3 END",
                (episode_id,),
            ).fetchall()
        return [self._file(row) for row in rows if row is not None]

    def save_channel_post(self, episode_id: int, chat_id: str, message_id: int) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO channel_posts(episode_id, chat_id, message_id)
                   VALUES (?, ?, ?)
                   ON CONFLICT(episode_id) DO UPDATE SET
                     chat_id = excluded.chat_id,
                     message_id = excluded.message_id,
                     updated_at = CURRENT_TIMESTAMP""",
                (episode_id, chat_id, message_id),
            )

    def channel_post(self, episode_id: int) -> tuple[str, int] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT chat_id, message_id FROM channel_posts WHERE episode_id = ?", (episode_id,)
            ).fetchone()
        return (str(row["chat_id"]), int(row["message_id"])) if row else None

    def counts(self) -> tuple[int, int]:
        with self._lock:
            episodes = self._connection.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            files = self._connection.execute("SELECT COUNT(*) FROM media_files").fetchone()[0]
        return int(episodes), int(files)

    def close(self) -> None:
        with self._lock:
            self._connection.close()
