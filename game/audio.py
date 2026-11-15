# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Audio manager for LunArk: Genesis.

Maps named events to audio files in audio/ folder.
Fails silently when files are absent (no crash on missing audio).
Respects master, music, and sfx volume from settings.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("lunark.audio")

# Root audio directory (audio/<name>.ogg)
AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"

# Named event → filename mapping (all in audio/)
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

# Volume range stored in settings as int 0–10 (displayed as 0–100)
MAX_VOL_STEPS = 10


def _vol(steps: int) -> float:
    """Convert 0–10 step to 0.0–1.0 pygame volume float."""
    return max(0.0, min(1.0, steps / MAX_VOL_STEPS))


class AudioManager:
    """Singleton-style audio manager. Silently ignores missing files and pygame errors."""

    def __init__(self) -> None:
        self._mixer_ok = False
        self._sounds: dict[str, Any] = {}   # name → pygame.mixer.Sound
        self._master: int = 8    # 0-10
        self._music: int = 7     # 0-10
        self._sfx: int = 8       # 0-10
        self._current_music: str | None = None

        self._try_init_mixer()

    def _try_init_mixer(self) -> None:
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._mixer_ok = True
        except Exception as exc:
            logger.debug("Audio mixer unavailable (silent mode): %s", exc)

    def apply_settings(self, settings: dict[str, Any]) -> None:
        """Update volume levels from settings dict."""
        self._master = int(settings.get("audio_master", self._master))
        self._music  = int(settings.get("audio_music",  self._music))
        self._sfx    = int(settings.get("audio_sfx",    self._sfx))
        self._update_music_volume()

    def _effective_sfx(self) -> float:
        return _vol(self._master) * _vol(self._sfx)

    def _effective_music(self) -> float:
        return _vol(self._master) * _vol(self._music)

    def _update_music_volume(self) -> None:
        if not self._mixer_ok:
            return
        try:
            import pygame
            pygame.mixer.music.set_volume(self._effective_music())
        except Exception:
            pass

    def play(self, name: str) -> None:
        """Play a named sound effect. No-op if file missing or mixer off."""
        if not self._mixer_ok:
            return
        if name not in SOUND_MAP:
            return
        try:
            import pygame
            if name not in self._sounds:
                path = AUDIO_DIR / SOUND_MAP[name]
                if not path.exists():
                    return
                self._sounds[name] = pygame.mixer.Sound(str(path))
            snd = self._sounds[name]
            snd.set_volume(self._effective_sfx())
            snd.play()
        except Exception as exc:
            logger.debug("Audio play '%s' failed: %s", name, exc)

    def play_music(self, name: str, loops: int = -1) -> None:
        """Start looping background music track. No-op if file missing."""
        if not self._mixer_ok or name == self._current_music:
            return
        if name not in MUSIC_MAP:
            return
        try:
            import pygame
            path = AUDIO_DIR / MUSIC_MAP[name]
            if not path.exists():
                return
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self._effective_music())
            pygame.mixer.music.play(loops)
            self._current_music = name
        except Exception as exc:
            logger.debug("Music '%s' failed: %s", name, exc)

    def stop_music(self) -> None:
        """Stop background music gracefully."""
        if not self._mixer_ok:
            return
        try:
            import pygame
            pygame.mixer.music.stop()
            self._current_music = None
        except Exception:
            pass


# Global singleton
audio = AudioManager()
