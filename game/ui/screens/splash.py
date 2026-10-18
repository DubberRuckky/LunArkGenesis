# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Splash screen displaying the LunArk logo with fade-in and fade-out.

Integer-scales the 33x33 pixel art logo to preserve crisp edges without blurring.
"""

import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_WHITE,
    FONT_SIZE_TITLE,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_TITLE,
    SPLASH_FADE_IN,
    SPLASH_FADE_OUT,
    SPLASH_HOLD,
)


class SplashScreen:
    """Displays introductory brand logo with smooth alpha fade transitions."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.elapsed: float = 0.0
        self.total_duration: float = SPLASH_FADE_IN + SPLASH_HOLD + SPLASH_FADE_OUT
        self.is_done: bool = False

        # Load logo asset
        self.raw_logo = assets.load_image("logo", default_size=(33, 33))
        # Integer scale logo by 3x (33x33 -> 99x99, approx 1/3 screen height)
        scale_factor = 3
        self.scaled_logo = pygame.transform.scale(
            self.raw_logo,
            (self.raw_logo.get_width() * scale_factor, self.raw_logo.get_height() * scale_factor),
        )
        self.logo_rect = self.scaled_logo.get_rect(
            center=(INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2)
        )

        self.font = assets.get_font(FONT_SIZE_TITLE)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Skip splash on any key press or mouse click."""
        for event in events:
            if event.type == pygame.KEYDOWN or (
                event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            ):
                self._finish()

    def update(self, dt: float) -> None:
        """Advance animation timer and switch screen upon completion."""
        self.elapsed += dt
        if self.elapsed >= self.total_duration:
            self._finish()

    def _finish(self) -> None:
        if not self.is_done:
            self.is_done = True
            # Switch to title screen
            self.app.set_screen(SCREEN_TITLE)  # type: ignore[attr-defined]

    def draw(self, surface: pygame.Surface) -> None:
        """Render black canvas, centered logo, and alpha curtain fade."""
        surface.fill(COLOR_BLACK)

        # Draw logo (or fallback text if logo is missing placeholder)
        if "logo" in assets.missing:
            txt_surf = self.font.render("LunArk", False, COLOR_WHITE)
            txt_rect = txt_surf.get_rect(center=(INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2))
            surface.blit(txt_surf, txt_rect)
        else:
            surface.blit(self.scaled_logo, self.logo_rect)

        # Calculate fade curtain alpha (0 = transparent, 255 = solid black)
        alpha = 0
        if self.elapsed < SPLASH_FADE_IN:
            # Fading in from black
            alpha = int(255 * (1.0 - (self.elapsed / SPLASH_FADE_IN)))
        elif self.elapsed < SPLASH_FADE_IN + SPLASH_HOLD:
            # Fully visible hold
            alpha = 0
        elif self.elapsed < self.total_duration:
            # Fading out to black
            fade_out_elapsed = self.elapsed - (SPLASH_FADE_IN + SPLASH_HOLD)
            alpha = int(255 * (fade_out_elapsed / SPLASH_FADE_OUT))
        else:
            alpha = 255

        if alpha > 0:
            curtain = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
            curtain.fill(COLOR_BLACK)
            curtain.set_alpha(max(0, min(255, alpha)))
            surface.blit(curtain, (0, 0))
