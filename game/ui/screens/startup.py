# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Startup introduction screen displaying a sequence of intro logo cards.

Plays three introduction cards (Team, Art, Engine) with smooth alpha fading,
black inter-card gaps, and single-card / full-sequence skipping.
"""

import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_WHITE,
    FONT_SIZE_LARGE,
    FONT_SIZE_SMALL,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_TITLE,
)
from game.logic.startup_sequence import StartupSequence


def scale_card_logo(logo_surf: pygame.Surface, scale_mode: str) -> pygame.Surface:
    """Scale a logo surface according to the card's specified scale mode.

    Args:
        logo_surf: Unscaled logo surface.
        scale_mode: 'integer' (nearest-neighbor upscaling) or 'fit' (smoothscale).

    Returns:
        pygame.Surface: Appropriately scaled surface.
    """
    w, h = logo_surf.get_size()

    if scale_mode == "integer":
        # Integer scaling: whole-number nearest-neighbor upscaling only.
        # If source was high-res export (e.g. 3300x3300 instead of 33x33), downscale to 33x33 first
        if w > 120 and w % 33 == 0 and h % 33 == 0:
            logo_surf = pygame.transform.scale(logo_surf, (33, 33))
            w, h = 33, 33
        elif w > 120 or h > 99:
            down = max(w // 120 + 1, h // 99 + 1)
            w = max(1, w // down)
            h = max(1, h // down)
            logo_surf = pygame.transform.scale(logo_surf, (w, h))

        # Upscale with largest integer factor that fits in 120x99 box (33x33 -> 99x99)
        factor = max(1, min(120 // w, 99 // h))
        return pygame.transform.scale(logo_surf, (w * factor, h * factor))

    elif scale_mode == "fit":
        # Fit mode: native size if it fits within 120x72 box, else smoothscale keeping aspect ratio
        max_w, max_h = 120, 72
        if w <= max_w and h <= max_h:
            return logo_surf
        scale = min(max_w / w, max_h / h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        return pygame.transform.smoothscale(logo_surf, (new_w, new_h))

    return logo_surf


class StartupScreen:
    """Renders the startup introduction card sequence with alpha transitions."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.sequence = StartupSequence()
        self.is_done: bool = False

        # Pre-render card graphic elements
        self._rendered_cards: list[dict] = []
        self._prepare_cards()

    def _prepare_cards(self) -> None:
        """Cache pre-rendered layout surfaces for each configured startup card."""
        self._rendered_cards = []

        # Mapping of relative logo path in startup.json to asset registry key
        path_to_key = {
            "logo/logo.png": "logo",
            "logo/aseprite.png": "logo_aseprite",
            "logo/pygame_ce.png": "logo_pygame_ce",
        }

        for card in self.sequence.cards:
            logo_rel = card.get("logo", "")
            asset_key = path_to_key.get(logo_rel, logo_rel)
            scale_mode = card.get("scale_mode", "fit")

            # Check if logo exists on disk or is missing
            logo_surface = None
            if asset_key:
                # load_image automatically records missing assets into assets.missing
                raw_logo = assets.load_image(asset_key)
                if asset_key not in assets.missing:
                    logo_surface = scale_card_logo(raw_logo, scale_mode)

            # Render text lines (size 11 or 22 only)
            rendered_lines: list[pygame.Surface] = []
            for line_def in card.get("lines", []):
                text = line_def.get("text", "")
                size = line_def.get("size", FONT_SIZE_LARGE)
                # Enforce multiple-of-11 font sizes
                font_size = FONT_SIZE_LARGE if size >= 22 else FONT_SIZE_SMALL
                font = assets.get_font(font_size)
                col = tuple(line_def.get("color", COLOR_WHITE))
                txt_surf = font.render(text, False, col)
                rendered_lines.append(txt_surf)

            # Calculate total group dimensions
            text_w = max((s.get_width() for s in rendered_lines), default=0)
            text_h = sum(s.get_height() for s in rendered_lines)

            gap = 12 if logo_surface and rendered_lines else 0
            logo_w = logo_surface.get_width() if logo_surface else 0
            logo_h = logo_surface.get_height() if logo_surface else 0

            group_w = max(logo_w, text_w)
            group_h = logo_h + gap + text_h

            # Construct cached card surface centered on screen
            card_surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
            card_surf.fill(COLOR_BLACK)

            start_y = (INTERNAL_HEIGHT - group_h) // 2

            # 1. Draw logo
            cur_y = start_y
            if logo_surface:
                lx = (INTERNAL_WIDTH - logo_w) // 2
                card_surf.blit(logo_surface, (lx, cur_y))
                cur_y += logo_h + gap

            # 2. Draw text lines
            for line_surf in rendered_lines:
                tx = (INTERNAL_WIDTH - line_surf.get_width()) // 2
                card_surf.blit(line_surf, (tx, cur_y))
                cur_y += line_surf.get_height()

            self._rendered_cards.append({
                "surface": card_surf,
            })

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Route user input for single-card skip or full-sequence abort."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Esc skips entire sequence directly to Title screen
                    self.sequence.skip_all()
                    self._finish()
                    return
                elif event.key not in (pygame.K_F11, pygame.K_F3):
                    # Any other key skips current card
                    self.sequence.skip_card()
                    if self.sequence.is_finished:
                        self._finish()
                    return

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left click skips current card
                self.sequence.skip_card()
                if self.sequence.is_finished:
                    self._finish()
                return

    def update(self, dt: float) -> None:
        """Advance startup sequence timeline."""
        self.sequence.update(dt)
        if self.sequence.is_finished:
            self._finish()

    def _finish(self) -> None:
        """Switch to title screen once introduction finishes."""
        if not self.is_done:
            self.is_done = True
            self.app.set_screen(SCREEN_TITLE)  # type: ignore[attr-defined]

    def draw(self, surface: pygame.Surface) -> None:
        """Render active card with modulated alpha onto target canvas."""
        surface.fill(COLOR_BLACK)

        if self.sequence.is_finished or self.sequence.in_gap:
            return

        idx = self.sequence.card_index
        alpha = self.sequence.alpha

        if 0 <= idx < len(self._rendered_cards) and alpha > 0:
            cached_surf = self._rendered_cards[idx]["surface"]
            if alpha == 255:
                cached_surf.set_alpha(None)
                surface.blit(cached_surf, (0, 0))
            else:
                cached_surf.set_alpha(alpha)
                surface.blit(cached_surf, (0, 0))


# Alias for backward compatibility
SplashScreen = StartupScreen
