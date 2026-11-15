# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Title screen for LunArk: Genesis.

Displays game logo/background and primary options: New Game, Continue, Settings, Quit.
"""

import random
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_GROUND,
    COLOR_SKY,
    COLOR_STAR,
    COLOR_WHITE,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_TITLE,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SAVEGAME_FILE,
    SCREEN_SETTINGS,
)
from game.ui.widgets import Button


class TitleScreen:
    """Main menu screen displaying game title and entry navigation buttons."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.title_font = assets.get_font(FONT_SIZE_TITLE)
        self.sub_font = assets.get_font(FONT_SIZE_LARGE)

        # Procedural starfield fallback cache
        random.seed(42)
        self.stars = [
            (random.randint(0, INTERNAL_WIDTH), random.randint(0, INTERNAL_HEIGHT - 60))
            for _ in range(70)
        ]

        # Has existing savegame?
        self.has_save = SAVEGAME_FILE.exists()

        # Build menu buttons centered vertically
        btn_w = 90
        btn_h = 18
        start_x = (INTERNAL_WIDTH - btn_w) // 2
        start_y = 135
        spacing = 22

        self.buttons: list[Button] = [
            Button(
                start_x,
                start_y,
                btn_w,
                btn_h,
                "New Game",
                self.font,
                callback=self._on_new_game,
            ),
            Button(
                start_x,
                start_y + spacing,
                btn_w,
                btn_h,
                "Continue",
                self.font,
                callback=self._on_continue,
                enabled=self.has_save,
            ),
            Button(
                start_x,
                start_y + spacing * 2,
                btn_w,
                btn_h,
                "Settings",
                self.font,
                callback=self._on_settings,
            ),
            Button(
                start_x,
                start_y + spacing * 3,
                btn_w,
                btn_h,
                "Quit",
                self.font,
                callback=self._on_quit,
            ),
        ]

    def _on_new_game(self) -> None:
        """Trigger start of new campaign / cutscene."""
        # For Phase 1, start game or notify (later cutscene/play screen)
        logger_name = "lunark.title"
        import logging
        logging.getLogger(logger_name).info("New Game clicked.")
        # Future phases transition to intro cutscene
        if hasattr(self.app, "start_new_game"):
            self.app.start_new_game()  # type: ignore[attr-defined]

    def _on_continue(self) -> None:
        """Resume existing savegame if available."""
        if hasattr(self.app, "continue_game"):
            self.app.continue_game()  # type: ignore[attr-defined]

    def _on_settings(self) -> None:
        """Open settings menu screen."""
        self.app.push_screen(SCREEN_SETTINGS)  # type: ignore[attr-defined]

    def _on_quit(self) -> None:
        """Exit the game application."""
        self.app.quit_game()  # type: ignore[attr-defined]

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Handle button interaction and keyboard shortcuts."""
        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]
        for btn in self.buttons:
            btn.update(events, mouse_pos)

    def update(self, dt: float) -> None:
        """Update save state check if file was created or removed."""
        self.has_save = SAVEGAME_FILE.exists()
        self.buttons[1].enabled = self.has_save

    def draw(self, surface: pygame.Surface) -> None:
        """Render background scenery, title banner, and menu buttons."""
        # 1. Background
        if "title_bg" not in assets.missing:
            bg_surf = assets.load_image("title_bg")
            surface.blit(bg_surf, (0, 0))
        else:
            # Code-drawn lunar night sky with stars and ground line
            surface.fill(COLOR_SKY)
            for sx, sy in self.stars:
                surface.set_at((sx, sy), COLOR_STAR)
            # Lunar ground horizon
            ground_rect = pygame.Rect(0, INTERNAL_HEIGHT - 45, INTERNAL_WIDTH, 45)
            pygame.draw.rect(surface, COLOR_GROUND, ground_rect)
            pygame.draw.line(surface, (150, 150, 145), (0, INTERNAL_HEIGHT - 45), (INTERNAL_WIDTH, INTERNAL_HEIGHT - 45), 1)

        # 2. Title Wordmark
        if "title" not in assets.missing:
            title_surf = assets.load_image("title")
            t_rect = title_surf.get_rect(center=(INTERNAL_WIDTH // 2, 60))
            surface.blit(title_surf, t_rect)
        else:
            # Code-rendered title typography
            title_txt = self.title_font.render("LunArk: Genesis", False, COLOR_WHITE)
            sub_txt = self.font.render("Lunar Outpost Simulation", False, (160, 190, 220))
            t_rect = title_txt.get_rect(center=(INTERNAL_WIDTH // 2, 55))
            s_rect = sub_txt.get_rect(center=(INTERNAL_WIDTH // 2, 85))
            surface.blit(title_txt, t_rect)
            surface.blit(sub_txt, s_rect)

        # 3. Menu Buttons
        for btn in self.buttons:
            btn.draw(surface)

        # Version stamp
        ver_surf = self.font.render("v0.1.0-alpha", False, (80, 85, 100))
        surface.blit(ver_surf, (6, INTERNAL_HEIGHT - 18))
