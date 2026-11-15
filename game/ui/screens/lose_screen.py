# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Defeat screen for LunArk: Genesis.

Displays defeat reason in plain words, exactly one hint chosen from text.json,
run statistics (cycles, buildings, science), and Play Again / Title buttons.
"""

from typing import Any
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_ERROR,
    COLOR_WHITE,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_GAME,
    SCREEN_TITLE,
)
from game.logic.data import load_text
from game.ui.widgets import Button, Panel


class LoseScreen:
    """Defeat screen explaining the loss cause with a helpful hint."""

    def __init__(
        self,
        app: object,
        cause: str = "energy",
        stats: dict[str, Any] | None = None,
        hint: str | None = None,
    ) -> None:
        self.app = app
        self.cause = cause
        self.stats = stats or {"cycles": 1, "buildings": 3, "science": 25}

        self.text_data = load_text().get("lose", {})
        self.title_font = assets.get_font(FONT_SIZE_LARGE)
        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.small_font = assets.get_font(FONT_SIZE_SMALL)

        # Select exactly one hint
        if hint:
            self.hint = hint
        elif cause == "boredom":
            hints = self.text_data.get("boredom_hints", ["Build recreational modules."])
            self.hint = hints[0] if hints else "Build Gyms and Cafes to keep crew happy."
        else:
            hints = self.text_data.get("energy_hints", ["Build extra fuel cells before night."])
            self.hint = hints[0] if hints else "Prepare battery reserves before dusk arrives."

        pw, ph = 330, 190
        px = (INTERNAL_WIDTH - pw) // 2
        py = (INTERNAL_HEIGHT - ph) // 2
        self.panel = Panel(px, py, pw, ph)

        try:
            from game.audio import audio
            audio.play("lose")
        except Exception:
            pass

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
                self.text_data.get("play_again", "Try Again"),
                self.font,
                callback=self._on_try_again,
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

    def _on_try_again(self) -> None:
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
        if "end_lose" not in assets.missing:
            surface.blit(assets.load_image("end_lose"), (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        self.panel.draw(surface)

        px = self.panel.rect.x
        py = self.panel.rect.y

        # Title
        title_txt = self.text_data.get("title", "Mission Failed")
        t_surf = self.title_font.render(title_txt, False, COLOR_ERROR)
        surface.blit(t_surf, (px + 14, py + 10))

        # Reason based on cause
        if self.cause == "boredom":
            reason_txt = self.text_data.get("boredom_reason", "The crew got too bored and left their posts.")
        else:
            reason_txt = self.text_data.get("energy_reason", "The base ran out of power for too long.")

        r_surf = self.small_font.render(reason_txt[:42], False, COLOR_WHITE)
        surface.blit(r_surf, (px + 14, py + 34))

        # Stats summary block
        cyc = self.stats.get("cycles", 1)
        bld = self.stats.get("buildings", 1)
        sci = int(self.stats.get("science", 0))
        stats_str = f"Cycles Survived: {cyc}  |  Buildings Built: {bld}  |  Science: {sci}"
        s_surf = self.small_font.render(stats_str, False, (220, 200, 180))
        surface.blit(s_surf, (px + 14, py + 54))

        # Exactly one hint
        hint_header = self.small_font.render("Mission Debrief Hint:", False, (255, 180, 120))
        surface.blit(hint_header, (px + 14, py + 74))

        h_surf = self.small_font.render(self.hint[:42], False, (255, 230, 200))
        surface.blit(h_surf, (px + 14, py + 90))

        for btn in self.buttons:
            btn.draw(surface)
