# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Pause modal overlay screen for LunArk: Genesis.

Displays resume, settings, save, load, and quit options.
Save/Load operate on slot 1 by default; a simple 3-slot picker
appears when the player clicks Save or Load.
"""

import pygame

from game.assets import assets
from game.constants import (
    COLOR_WHITE,
    COLOR_ENERGY,
    COLOR_ERROR,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_SETTINGS,
    SCREEN_TITLE,
)
from game.logic.data import load_text
from game.logic.save_load import slot_info
from game.ui.widgets import Button, Panel


class PauseScreen:
    """Modal pause screen overlaid on the running simulation."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.text_data = load_text().get("pause", {})
        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.small_font = assets.get_font(FONT_SIZE_SMALL)
        self.title_font = assets.get_font(FONT_SIZE_LARGE)

        # Slot picker overlay state: None | "save" | "load"
        self._slot_mode: str | None = None
        self._status_msg: str = ""
        self._status_timer: float = 0.0

        # Main panel geometry (5 buttons now)
        pw, ph = 180, 178
        px = (INTERNAL_WIDTH - pw) // 2
        py = (INTERNAL_HEIGHT - ph) // 2
        self.panel = Panel(px, py, pw, ph)

        btn_w, btn_h = 120, 20
        bx = (INTERNAL_WIDTH - btn_w) // 2
        by = py + 38
        step = 26

        self.buttons = [
            Button(bx, by,          btn_w, btn_h, self.text_data.get("resume",       "Resume"),        self.font, callback=self._on_resume),
            Button(bx, by + step,   btn_w, btn_h, self.text_data.get("settings",     "Settings"),      self.font, callback=self._on_settings),
            Button(bx, by + step*2, btn_w, btn_h, self.text_data.get("save",         "Save Game"),     self.font, callback=self._on_save),
            Button(bx, by + step*3, btn_w, btn_h, self.text_data.get("load",         "Load Game"),     self.font, callback=self._on_load),
            Button(bx, by + step*4, btn_w, btn_h, self.text_data.get("quit_to_title","Quit to Title"), self.font, callback=self._on_quit_title),
        ]

        # Slot picker panel (3 slot buttons)
        sp_w, sp_h = 240, 100
        sp_x = (INTERNAL_WIDTH - sp_w) // 2
        sp_y = (INTERNAL_HEIGHT - sp_h) // 2
        self.slot_panel = Panel(sp_x, sp_y, sp_w, sp_h)

        sb_y = sp_y + 32
        sb_w, sb_h = 60, 18
        sb_gap = 10
        total_sb_w = 3 * sb_w + 2 * sb_gap
        sb_x0 = sp_x + (sp_w - total_sb_w) // 2

        self.slot_buttons: list[Button] = []
        for i in range(3):
            slot_num = i + 1
            self.slot_buttons.append(Button(
                sb_x0 + i * (sb_w + sb_gap),
                sb_y,
                sb_w,
                sb_h,
                f"Slot {slot_num}",
                self.font,
                callback=lambda s=slot_num: self._on_slot_chosen(s),
            ))

        self.btn_slot_cancel = Button(
            (INTERNAL_WIDTH - 60) // 2,
            sp_y + sp_h - 24,
            60, 18,
            "Cancel",
            self.font,
            callback=lambda: setattr(self, "_slot_mode", None),
        )

    # ------------------------------------------------------------------

    def _on_resume(self) -> None:
        if hasattr(self.app, "pop_screen"):
            self.app.pop_screen()  # type: ignore[attr-defined]

    def _on_settings(self) -> None:
        if hasattr(self.app, "push_screen"):
            self.app.push_screen(SCREEN_SETTINGS)  # type: ignore[attr-defined]

    def _on_save(self) -> None:
        self._slot_mode = "save"

    def _on_load(self) -> None:
        self._slot_mode = "load"

    def _on_quit_title(self) -> None:
        if hasattr(self.app, "set_screen"):
            self.app.set_screen(SCREEN_TITLE)  # type: ignore[attr-defined]

    def _on_slot_chosen(self, slot: int) -> None:
        """Save or load from chosen slot, then close picker."""
        # Walk up the stack to find GameScreen
        game_screen = None
        stack = getattr(self.app, "screen_stack", [])
        for s in stack:
            if type(s).__name__ == "GameScreen":
                game_screen = s
                break

        if self._slot_mode == "save":
            if game_screen is not None:
                from game.logic.save_load import save_game
                ok = save_game(
                    slot=slot,
                    player_name=getattr(game_screen, "player_name", "Commander"),
                    play_time=getattr(game_screen, "play_time", 0.0),
                    state=game_screen.state,
                    world_grid=game_screen.world_grid,
                    lunar_clock=game_screen.lunar_clock,
                    objectives=game_screen.objective_manager,
                )
                self._status_msg = f"Saved to slot {slot}!" if ok else "Save failed."
            else:
                self._status_msg = "Nothing to save yet."

        elif self._slot_mode == "load":
            if game_screen is not None:
                from game.logic.save_load import load_game, apply_save
                data = load_game(slot)
                if data is not None:
                    name = apply_save(data, game_screen.state, game_screen.world_grid,
                                     game_screen.lunar_clock, game_screen.objective_manager)
                    game_screen.player_name = name
                    self._status_msg = f"Loaded slot {slot}!"
                else:
                    self._status_msg = f"Slot {slot} is empty."
            else:
                self._status_msg = "Cannot load here."

        self._slot_mode = None
        self._status_timer = 2.5

    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self._slot_mode is not None:
                    self._slot_mode = None
                else:
                    self._on_resume()
                return

        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]

        if self._slot_mode is not None:
            for sb in self.slot_buttons:
                sb.update(events, mouse_pos)
            self.btn_slot_cancel.update(events, mouse_pos)
            return

        for btn in self.buttons:
            btn.update(events, mouse_pos)

    def update(self, dt: float) -> None:
        if self._status_timer > 0:
            self._status_timer -= dt

    def draw(self, surface: pygame.Surface) -> None:
        # Dim background
        dim_surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 150))
        surface.blit(dim_surf, (0, 0))

        self.panel.draw(surface)

        title_text = self.text_data.get("title", "Base Paused")
        txt_surf = self.title_font.render(title_text, False, COLOR_WHITE)
        tx = (INTERNAL_WIDTH - txt_surf.get_width()) // 2
        surface.blit(txt_surf, (tx, self.panel.rect.y + 12))

        for btn in self.buttons:
            btn.draw(surface)

        # Status message (brief confirm/error after save/load)
        if self._status_timer > 0 and self._status_msg:
            col = COLOR_ENERGY if "!" in self._status_msg else COLOR_ERROR
            sm = self.small_font.render(self._status_msg, False, col)
            surface.blit(sm, (sm.get_rect(centerx=INTERNAL_WIDTH // 2).x,
                               self.panel.rect.bottom + 4))

        # Slot picker overlay
        if self._slot_mode is not None:
            self._draw_slot_picker(surface)

    def _draw_slot_picker(self, surface: pygame.Surface) -> None:
        """Draw the 3-slot selection overlay."""
        self.slot_panel.draw(surface)
        verb = "Save to" if self._slot_mode == "save" else "Load from"
        hdr = self.font.render(f"{verb} which slot?", False, COLOR_WHITE)
        surface.blit(hdr, (hdr.get_rect(centerx=INTERNAL_WIDTH // 2).x,
                            self.slot_panel.rect.y + 10))

        for i, sb in enumerate(self.slot_buttons):
            sb.draw(surface)
            info = slot_info(i + 1)
            if info:
                lbl = self.small_font.render(
                    f"{info['player_name']} Cy{info['cycle']}",
                    False, (160, 180, 200)
                )
                surface.blit(lbl, (sb.rect.x, sb.rect.bottom + 2))
            else:
                empty = self.small_font.render("empty", False, (90, 95, 110))
                surface.blit(empty, (sb.rect.x, sb.rect.bottom + 2))

        self.btn_slot_cancel.draw(surface)
