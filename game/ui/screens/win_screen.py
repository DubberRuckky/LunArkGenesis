# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Victory screen for LunArk: Genesis.

Displays victory debriefing, reason, one selected hint, mission stats,
and navigation buttons (Play Again, Back to Title).
"""

from typing import Any
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_ENERGY,
    COLOR_WHITE,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    ICON,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_GAME,
    SCREEN_TITLE,
)
from game.logic.data import load_text
from game.ui.widgets import Button, Panel


class WinScreen:
    """Victory screen with mission debriefing, hint, stats, and navigation buttons."""

    def __init__(
        self,
        app: object,
        stats: dict[str, Any] | None = None,
        hint: str | None = None,
    ) -> None:
        self.app = app
        self.stats = stats or {"cycles": 3, "buildings": 8, "science": 120}
        self.hint = hint or "A happy crew and steady generators ensure lunar base survival."

        try:
            from game.audio import audio
            audio.play("win")
        except Exception:
            pass

        self.text_data = load_text().get("win", {})
        self.title_font = assets.get_font(FONT_SIZE_LARGE)
        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.small_font = assets.get_font(FONT_SIZE_SMALL)

        pw, ph = 330, 190
        px = (INTERNAL_WIDTH - pw) // 2
        py = (INTERNAL_HEIGHT - ph) // 2
        self.panel = Panel(px, py, pw, ph)

        btn_w, btn_h = 105, 20
        spacing = 16
        total_w = btn_w * 2 + spacing
        bx1 = (INTERNAL_WIDTH - total_w) // 2
        bx2 = bx1 + btn_w + spacing
        by = py + ph - 28

        self.buttons = [
            Button(
                bx1,
                by,
                btn_w,
                btn_h,
                self.text_data.get("play_again", "Play Again"),
                self.font,
                callback=self._on_play_again,
            ),
            Button(
                bx2,
                by,
                btn_w,
                btn_h,
                self.text_data.get("back_to_title", "Back to Title"),
                self.font,
                callback=self._on_title,
            ),
        ]

    def _on_play_again(self) -> None:
        if hasattr(self.app, "set_screen"):
            self.app.set_screen(SCREEN_GAME)  # type: ignore[attr-defined]

    def _on_title(self) -> None:
        if hasattr(self.app, "set_screen"):
            self.app.set_screen(SCREEN_TITLE)  # type: ignore[attr-defined]

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]
        for btn in self.buttons:
            btn.update(events, mouse_pos)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        # Background: end_win image or dark background
        if "end_win" not in assets.missing:
            surface.blit(assets.load_image("end_win"), (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        self.panel.draw(surface)

        px = self.panel.rect.x
        py = self.panel.rect.y

        # Title with checkmark icon
        check_icon = assets.get_icon(ICON.get("check", 21))
        surface.blit(check_icon, (px + 12, py + 12))

        title_txt = self.text_data.get("title", "Mission Accomplished!")
        t_surf = self.title_font.render(title_txt, False, COLOR_ENERGY)
        surface.blit(t_surf, (px + 34, py + 10))

        # Reason
        reason_txt = self.text_data.get("reason", "You completed Planet Stats and survived 3 lunar days!")
        r_surf = self.small_font.render(reason_txt[:42], False, COLOR_WHITE)
        surface.blit(r_surf, (px + 12, py + 34))

        # Stats summary block
        cyc = self.stats.get("cycles", 3)
        bld = self.stats.get("buildings", 1)
        sci = int(self.stats.get("science", 100))
        stats_str = f"Cycles Survived: {cyc}/3  |  Buildings Built: {bld}  |  Science: {sci}"
        s_surf = self.small_font.render(stats_str, False, (180, 240, 180))
        surface.blit(s_surf, (px + 12, py + 54))

        # Exactly one hint
        hint_header = self.small_font.render("Commander's Log / Tip:", False, (140, 180, 240))
        surface.blit(hint_header, (px + 12, py + 74))

        h_surf = self.small_font.render(self.hint[:42], False, (220, 230, 255))
        surface.blit(h_surf, (px + 12, py + 90))

        for btn in self.buttons:
            btn.draw(surface)
