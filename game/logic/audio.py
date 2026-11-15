# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Audio data constants and pure-Python audio stub for game/logic.

Pure Python — NO pygame imports.
Hardware audio playback resides in game.audio.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("lunark.logic.audio")

# Named event mapping definitions
SOUND_MAP: dict[str, str] = {
    "click":       "click.ogg",
    "build":       "build.ogg",
    "error":       "error.ogg",
    "warning":     "warning.ogg",
    "flare":       "flare.ogg",
    "night_start": "night_start.ogg",
    "win":         "win.ogg",
    "lose":        "lose.ogg",
}
MUSIC_MAP: dict[str, str] = {
    "music_day":   "music_day.ogg",
    "music_night": "music_night.ogg",
}

MAX_VOL_STEPS = 10


def _vol(steps: int) -> float:
    """Convert 0–10 step to 0.0–1.0 volume float."""
    return max(0.0, min(1.0, steps / MAX_VOL_STEPS))


class PureAudioManager:
    """Headless/pure audio controller that tracks volume without importing pygame."""

    def __init__(self) -> None:
        self._master: int = 8
        self._music: int = 7
        self._sfx: int = 8
        self._current_music: str | None = None

    def apply_settings(self, settings: dict[str, Any]) -> None:
        self._master = int(settings.get("audio_master", self._master))
        self._music  = int(settings.get("audio_music",  self._music))
        self._sfx    = int(settings.get("audio_sfx",    self._sfx))

    def play(self, name: str) -> None:
        pass

    def play_music(self, name: str, loops: int = -1) -> None:
        self._current_music = name

    def stop_music(self) -> None:
        self._current_music = None


audio = PureAudioManager()
