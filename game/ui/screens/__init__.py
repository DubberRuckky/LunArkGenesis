# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Game screens — each screen is a state in the screen manager."""

from game.ui.screens.game_screen import GameScreen
from game.ui.screens.lose_screen import LoseScreen
from game.ui.screens.pause_screen import PauseScreen
from game.ui.screens.settings_menu import SettingsScreen
from game.ui.screens.startup import StartupScreen
from game.ui.screens.title import TitleScreen
from game.ui.screens.win_screen import WinScreen

__all__ = [
    "GameScreen",
    "LoseScreen",
    "PauseScreen",
    "SettingsScreen",
    "StartupScreen",
    "TitleScreen",
    "WinScreen",
]
