# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Integration test for screen navigation and stub screens.

Runs headless with SDL dummy video driver.
Verifies Start -> Game -> Pause -> Resume / Quit to Title,
and debug F4 (Win) / F5 (Lose) navigation.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pytest

from game.app import App
from game.constants import SCREEN_GAME, SCREEN_LOSE, SCREEN_PAUSE, SCREEN_TITLE, SCREEN_WIN
from game.ui.screens.game_screen import GameScreen
from game.ui.screens.intro_screen import IntroScreen
from game.ui.screens.lose_screen import LoseScreen
from game.ui.screens.pause_screen import PauseScreen
from game.ui.screens.title import TitleScreen
from game.ui.screens.win_screen import WinScreen


@pytest.fixture
def app_instance():
    """Create a headless App instance with startup skipped and debug enabled."""
    app = App(skip_startup=True, debug=True)
    yield app
    app.quit_game()


def test_app_starts_on_title(app_instance: App) -> None:
    """Verifies that skipping startup opens directly on TitleScreen."""
    current = app_instance.get_current_screen()
    assert isinstance(current, TitleScreen)


def test_start_opens_game_stub(app_instance: App) -> None:
    """Verifies that starting a new game transitions from TitleScreen to IntroScreen (Stage 8)."""
    title_screen = app_instance.get_current_screen()
    assert isinstance(title_screen, TitleScreen)

    title_screen._on_new_game()
    current = app_instance.get_current_screen()
    # Stage 8: New Game now shows the Intro/Tutorial screen first
    assert isinstance(current, IntroScreen)


def test_game_esc_opens_pause_and_resume(app_instance: App) -> None:
    """Verifies Esc opens PauseScreen, and resume pops back to GameScreen."""
    app_instance.set_screen(SCREEN_GAME)
    game_screen = app_instance.get_current_screen()
    assert isinstance(game_screen, GameScreen)

    # Press Esc
    esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    game_screen.handle_events([esc_event])

    current = app_instance.get_current_screen()
    assert isinstance(current, PauseScreen)

    # Resume from Pause
    current._on_resume()
    assert isinstance(app_instance.get_current_screen(), GameScreen)


def test_pause_quit_to_title(app_instance: App) -> None:
    """Verifies Quit to Title in Pause menu switches back to TitleScreen."""
    app_instance.set_screen(SCREEN_GAME)
    app_instance.push_screen(SCREEN_PAUSE)
    pause_screen = app_instance.get_current_screen()
    assert isinstance(pause_screen, PauseScreen)

    pause_screen._on_quit_title()
    assert isinstance(app_instance.get_current_screen(), TitleScreen)


def test_debug_f4_f5_navigation(app_instance: App) -> None:
    """Verifies F4 opens WinScreen and F5 opens LoseScreen when debug is enabled."""
    app_instance.set_screen(SCREEN_GAME)
    game_screen = app_instance.get_current_screen()

    # F4 -> Win
    f4_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4)
    game_screen.handle_events([f4_event])
    assert isinstance(app_instance.get_current_screen(), WinScreen)

    # WinScreen back to Title
    win_screen = app_instance.get_current_screen()
    win_screen._on_title()
    assert isinstance(app_instance.get_current_screen(), TitleScreen)

    # Back to game, then F5 -> Lose
    app_instance.set_screen(SCREEN_GAME)
    game_screen = app_instance.get_current_screen()
    f5_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F5)
    game_screen.handle_events([f5_event])
    assert isinstance(app_instance.get_current_screen(), LoseScreen)


def test_game_automatic_win_and_lose_transitions(app_instance: App) -> None:
    """Verifies that GameScreen transitions to WinScreen or LoseScreen when objectives fire."""
    app_instance.set_screen(SCREEN_GAME)
    game_screen = app_instance.get_current_screen()
    assert isinstance(game_screen, GameScreen)

    # Force win condition
    game_screen.objectives.is_won = True
    game_screen.update(1.0)
    current = app_instance.get_current_screen()
    assert isinstance(current, WinScreen)
    assert current.hint != ""

    # Back to game and force defeat condition
    app_instance.set_screen(SCREEN_GAME)
    game_screen = app_instance.get_current_screen()
    game_screen.objectives.is_lost = True
    game_screen.objectives.lose_cause = "energy"
    game_screen.update(1.0)
    current = app_instance.get_current_screen()
    assert isinstance(current, LoseScreen)
    assert current.cause == "energy"
    assert current.hint != ""
