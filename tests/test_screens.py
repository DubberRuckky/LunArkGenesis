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


def test_all_screens_draw_headless_at_mouse_positions(app_instance: App) -> None:
    """Verifies that EVERY screen renders without exceptions across various mouse positions.

    Tests Title, Intro, Game, Pause, Settings, Win, and Lose screens,
    specifically testing hover and non-hover states for all interactive widgets.
    """
    from game.constants import SCREEN_SETTINGS

    screens_to_test = [
        (SCREEN_TITLE, TitleScreen),
        ("intro", IntroScreen),
        (SCREEN_GAME, GameScreen),
        (SCREEN_PAUSE, PauseScreen),
        (SCREEN_SETTINGS, None),
        (SCREEN_WIN, WinScreen),
        (SCREEN_LOSE, LoseScreen),
    ]

    canvas = app_instance.display.canvas

    for screen_name, expected_cls in screens_to_test:
        app_instance.set_screen(screen_name)
        screen = app_instance.get_current_screen()
        if expected_cls:
            assert isinstance(screen, expected_cls)

        # Collect key points to sample: corners, center, and every button center
        positions: list[tuple[int, int]] = [(0, 0), (240, 135), (479, 269), (10, 10), (400, 250)]

        # Find buttons or rects on the screen
        if hasattr(screen, "buttons"):
            for btn in getattr(screen, "buttons", []):
                if hasattr(btn, "rect"):
                    positions.append(btn.rect.center)
                    # Also sample just outside the button to test non-hover
                    positions.append((btn.rect.x - 2, btn.rect.y - 2))

        if hasattr(screen, "build_tray"):
            tray = screen.build_tray
            for r in getattr(tray, "tab_rects", {}).values():
                positions.append(r.center)
            if hasattr(tray, "demolish_rect"):
                positions.append(tray.demolish_rect.center)
            for cr in getattr(tray, "card_rects", []):
                positions.append(cr.center)

        if hasattr(screen, "hud"):
            hud = screen.hud
            for br in getattr(hud, "bar_rects", {}).values():
                positions.append(br.center)
            for btn in getattr(hud, "speed_buttons", []):
                if "rect" in btn:
                    positions.append(btn["rect"].center)

        for pos in positions:
            # Mock canvas mouse pos on app
            app_instance.get_canvas_mouse_pos = lambda p=pos: p  # type: ignore[assignment]

            # Update & handle events with this mouse position
            motion_event = pygame.event.Event(pygame.MOUSEMOTION, pos=pos)
            screen.handle_events([motion_event])
            screen.update(0.05)

            # Draw onto canvas - must not raise any exception (e.g. ValueError: invalid color)
            screen.draw(canvas)


def test_settings_menu_sizing_and_wrapping(app_instance: App) -> None:
    """Verifies SettingsMenu sizing, screen bounds fitting, centering, and text wrapping."""
    from game.ui.screens.settings_menu import SettingsMenu, SettingsScreen
    from game.ui.widgets import wrap_text, wrap_text_to_width, draw_text
    import pygame

    assert SettingsMenu is SettingsScreen

    menu = SettingsScreen(app_instance)

    # 1. Verify menu panel is centered and fits completely inside the 480x270 screen
    screen_rect = pygame.Rect(0, 0, 480, 270)
    assert screen_rect.contains(menu.panel.rect), (
        f"Settings panel {menu.panel.rect} exceeds screen {screen_rect}"
    )
    assert menu.panel.rect.centerx == 240
    assert menu.panel.rect.centery == 135

    # 2. Verify all interactive controls fit inside the panel
    controls = [
        menu.mode_selector,
        menu.res_selector,
        menu.fps_selector,
        menu.toggle_vsync,
        menu.toggle_int_scale,
        menu.toggle_show_fps,
        menu.audio_master_sel,
        menu.audio_music_sel,
        menu.audio_sfx_sel,
        menu.btn_apply,
        menu.btn_reset,
        menu.btn_back,
    ]
    for ctrl in controls:
        r = getattr(ctrl, "rect", None) or getattr(ctrl, "pill_rect", None)
        assert r is not None
        assert menu.panel.rect.contains(r), (
            f"Control {ctrl} rect {r} is outside settings panel {menu.panel.rect}"
        )

    # 3. Verify resize method re-centers
    menu.resize(480, 270)
    assert menu.panel.rect.centerx == 240
    assert menu.panel.rect.centery == 135

    # 4. Verify text wrapping helpers
    font = menu.font
    sample = "Astronaut training requires careful module management and high vigilance during lunar nightfall."
    wrapped = wrap_text(sample, font, 100)
    for line in wrapped:
        assert font.size(line)[0] <= 100, f"Line '{line}' exceeds max width 100"

    # Single very long word wrapping
    long_word = "Supercalifragilisticexpialidocious"
    wrapped_long = wrap_text_to_width(long_word, font, 60)
    for line in wrapped_long:
        assert font.size(line)[0] <= 60

    # Draw text test
    test_surf = pygame.Surface((200, 200))
    end_y = draw_text(test_surf, "Test line 1\nTest line 2", font, (255, 255, 255), 10, 10, max_width=150)
    assert end_y > 10


