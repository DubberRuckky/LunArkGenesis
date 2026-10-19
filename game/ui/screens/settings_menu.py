# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Settings menu screen with restart confirmation modal.

Allows tuning display mode, resolution, FPS cap, VSync, integer scaling,
and performance metrics. Display changes take effect upon application restart.
"""

from copy import deepcopy
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_ERROR,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_REMINDER,
    COLOR_WHITE,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FPS_OPTIONS,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
)
from game.logic.settings import (
    get_defaults,
    needs_restart,
    validate_settings,
)
from game.ui.widgets import Button, OptionSelector, Panel, Toggle


class SettingsScreen:
    """Full settings interface with video, display, and rendering options."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.header_font = assets.get_font(FONT_SIZE_LARGE)

        # Open with SAVED settings (what will happen after restart)
        self.saved_settings = deepcopy(self.app.saved_settings)  # type: ignore[attr-defined]
        self.pending_settings = deepcopy(self.saved_settings)

        # Restart confirmation modal state
        self.modal_active: bool = False
        self.modal_error: str | None = None

        # Gather resolutions that fit desktop
        available_tuples = self.app.display.get_available_resolutions()  # type: ignore[attr-defined]
        self.res_tuples: list[tuple[int, int]] = available_tuples
        self.res_strings: list[str] = [f"{w}x{h}" for w, h in self.res_tuples]

        # Active resolution index
        cur_res = tuple(self.pending_settings.get("resolution", (1280, 720)))
        if cur_res in self.res_tuples:
            res_idx = self.res_tuples.index(cur_res)
        else:
            res_idx = 0

        # FPS options: 30, 60, 120, 144, 0 (Unlimited)
        self.fps_values = FPS_OPTIONS
        self.fps_strings = [str(f) if f > 0 else "Unlimited" for f in self.fps_values]
        cur_fps = self.pending_settings.get("fps_cap", 60)
        fps_idx = self.fps_values.index(cur_fps) if cur_fps in self.fps_values else 1

        # Container panel layout
        panel_w = 340
        panel_h = 246
        panel_x = (INTERNAL_WIDTH - panel_w) // 2
        panel_y = (INTERNAL_HEIGHT - panel_h) // 2
        self.panel = Panel(panel_x, panel_y, panel_w, panel_h)

        row_x = panel_x + 18
        row_w = panel_w - 36
        start_y = panel_y + 46
        line_step = 28

        # 1. Display mode selector
        self.mode_selector = OptionSelector(
            row_x,
            start_y,
            row_w,
            "Display Mode",
            ["Fullscreen", "Windowed"],
            self.font,
            selected_index=0 if self.pending_settings.get("fullscreen") else 1,
            callback=self._on_mode_changed,
        )

        # 2. Resolution selector
        self.res_selector = OptionSelector(
            row_x,
            start_y + line_step,
            row_w,
            "Resolution",
            self.res_strings,
            self.font,
            selected_index=res_idx,
            callback=self._on_res_changed,
            enabled=not self.pending_settings.get("fullscreen"),
        )
        self.res_selector.set_note("Fullscreen uses desktop resolution.")

        # 3. FPS Cap selector
        self.fps_selector = OptionSelector(
            row_x,
            start_y + line_step * 2,
            row_w,
            "FPS Cap",
            self.fps_strings,
            self.font,
            selected_index=fps_idx,
            callback=self._on_fps_changed,
        )

        # 4. VSync toggle
        self.toggle_vsync = Toggle(
            row_x,
            start_y + line_step * 3,
            "VSync (smooth screen sync)",
            self.font,
            value=self.pending_settings.get("vsync", True),
            callback=self._on_vsync_changed,
        )

        # 5. Show FPS toggle
        self.toggle_show_fps = Toggle(
            row_x,
            start_y + line_step * 4,
            "Show FPS Counter",
            self.font,
            value=self.pending_settings.get("show_fps", False),
            callback=self._on_show_fps_changed,
        )

        # 6. Integer scaling toggle
        self.toggle_int_scale = Toggle(
            row_x,
            start_y + line_step * 5,
            "Integer Scaling (crisp pixels)",
            self.font,
            value=self.pending_settings.get("integer_scaling", True),
            callback=self._on_int_scale_changed,
        )

        # Action buttons
        btn_y = panel_y + panel_h - 26
        btn_w = 56
        btn_h = 18

        self.btn_apply = Button(
            panel_x + 18,
            btn_y,
            btn_w,
            btn_h,
            "Apply",
            self.font,
            callback=self._on_apply,
        )
        self.btn_reset = Button(
            panel_x + 18 + btn_w + 8,
            btn_y,
            btn_w + 48,
            btn_h,
            "Reset Defaults",
            self.font,
            callback=self._on_reset,
        )
        self.btn_back = Button(
            panel_x + panel_w - btn_w - 18,
            btn_y,
            btn_w,
            btn_h,
            "Back",
            self.font,
            callback=self._on_back,
        )

        # Restart confirmation modal layout
        modal_w = 350
        modal_h = 104
        modal_x = (INTERNAL_WIDTH - modal_w) // 2
        modal_y = (INTERNAL_HEIGHT - modal_h) // 2
        self.modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        # Modal buttons: Restart Now (width 100), Later (width 64)
        btn_restart_w = 100
        btn_later_w = 64
        btn_gap = 16
        total_btn_w = btn_restart_w + btn_gap + btn_later_w
        modal_btn_x = modal_x + (modal_w - total_btn_w) // 2
        modal_btn_y = modal_y + 70

        self.btn_restart_now = Button(
            modal_btn_x,
            modal_btn_y,
            btn_restart_w,
            20,
            "Restart Now",
            self.font,
            callback=self._on_restart_now,
        )
        self.btn_later = Button(
            modal_btn_x + btn_restart_w + btn_gap,
            modal_btn_y,
            btn_later_w,
            20,
            "Later",
            self.font,
            callback=self._on_later,
        )

    # -----------------------------------------------------------------------
    # Widget Callbacks
    # -----------------------------------------------------------------------

    def _on_mode_changed(self, idx: int, text: str) -> None:
        is_fs = (idx == 0)
        self.pending_settings["fullscreen"] = is_fs
        self.res_selector.set_enabled(not is_fs)

    def _on_res_changed(self, idx: int, text: str) -> None:
        if idx < len(self.res_tuples):
            self.pending_settings["resolution"] = list(self.res_tuples[idx])

    def _on_fps_changed(self, idx: int, text: str) -> None:
        if idx < len(self.fps_values):
            self.pending_settings["fps_cap"] = self.fps_values[idx]

    def _on_vsync_changed(self, val: bool) -> None:
        self.pending_settings["vsync"] = val

    def _on_show_fps_changed(self, val: bool) -> None:
        self.pending_settings["show_fps"] = val

    def _on_int_scale_changed(self, val: bool) -> None:
        self.pending_settings["integer_scaling"] = val

    def _on_reset(self) -> None:
        """Reset pending controls to default settings values."""
        defaults = get_defaults()
        self.pending_settings = deepcopy(defaults)
        self._sync_widgets_from_settings(self.pending_settings)

    def _on_apply(self) -> None:
        """Validate, apply live settings, and save. Open modal if restart needed."""
        cleaned = validate_settings(
            self.pending_settings,
            available_resolutions=self.res_tuples,
            extra_resolutions=self.app.desktop_size,  # type: ignore[attr-defined]
        )
        self.pending_settings = cleaned

        # Apply live settings and save all settings to disk
        self.app.apply_saved_settings(self.pending_settings)  # type: ignore[attr-defined]
        self.saved_settings = deepcopy(self.pending_settings)

        # If any restart-needed setting differs from running game, show modal
        if needs_restart(self.app.running_settings, self.saved_settings):  # type: ignore[attr-defined]
            self.modal_active = True
            self.modal_error = None
        else:
            self.modal_active = False
            self.modal_error = None

    def _on_restart_now(self) -> None:
        """Attempt to launch a new copy of the game and terminate this process."""
        success = self.app.restart_game()  # type: ignore[attr-defined]
        if not success:
            self.modal_error = "Restart failed. Please start the game again."

    def _on_later(self) -> None:
        """Dismiss the modal; pending restart changes apply on next launch."""
        self.modal_active = False
        self.modal_error = None

    def _sync_widgets_from_settings(self, st: dict) -> None:
        """Sync UI controls with settings dict values."""
        self.mode_selector.set_index(0 if st.get("fullscreen") else 1)
        self.res_selector.set_enabled(not st.get("fullscreen"))
        cur_res = tuple(st.get("resolution", (1280, 720)))
        if cur_res in self.res_tuples:
            self.res_selector.set_index(self.res_tuples.index(cur_res))
        cur_fps = st.get("fps_cap", 60)
        if cur_fps in self.fps_values:
            self.fps_selector.set_index(self.fps_values.index(cur_fps))
        self.toggle_vsync.value = st.get("vsync", True)
        self.toggle_show_fps.value = st.get("show_fps", False)
        self.toggle_int_scale.value = st.get("integer_scaling", True)

    def _on_back(self) -> None:
        """Return to previous screen (Title or Pause)."""
        self.app.pop_screen()  # type: ignore[attr-defined]

    # -----------------------------------------------------------------------
    # Event & Update Loop
    # -----------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Route input events to modal or main settings controls."""
        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]

        # Handle ESC key: Later if modal active, otherwise Back
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.modal_active:
                    self._on_later()
                else:
                    self._on_back()
                return

        # Modal interaction blocks background settings controls
        if self.modal_active:
            self.btn_restart_now.update(events, mouse_pos)
            self.btn_later.update(events, mouse_pos)
            return

        # Main settings interaction
        self.mode_selector.update(events, mouse_pos)
        self.res_selector.update(events, mouse_pos)
        self.fps_selector.update(events, mouse_pos)
        self.toggle_vsync.update(events, mouse_pos)
        self.toggle_show_fps.update(events, mouse_pos)
        self.toggle_int_scale.update(events, mouse_pos)

        self.btn_apply.update(events, mouse_pos)
        self.btn_reset.update(events, mouse_pos)
        self.btn_back.update(events, mouse_pos)

    def update(self, dt: float) -> None:
        """Update settings screen state."""
        # Sync fullscreen control if F11 toggled it externally
        fs_saved = self.app.saved_settings.get("fullscreen", True)  # type: ignore[attr-defined]
        if self.saved_settings.get("fullscreen") != fs_saved:
            self.saved_settings["fullscreen"] = fs_saved
            self.pending_settings["fullscreen"] = fs_saved
            self.mode_selector.set_index(0 if fs_saved else 1)
            self.res_selector.set_enabled(not fs_saved)

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Render settings panel, all controls, and optional modal overlay."""
        # Backdrop dim
        dim = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        dim.fill((5, 5, 10, 180))
        surface.blit(dim, (0, 0))

        # Panel frame
        self.panel.draw(surface)

        # Header Title
        title_surf = self.header_font.render("Settings", False, COLOR_WHITE)
        surface.blit(title_surf, (self.panel.rect.x + 18, self.panel.rect.y + 10))

        # Orange restart reminder in header if restart is pending
        if self.app.is_restart_pending():  # type: ignore[attr-defined]
            rem_surf = self.font.render("Restart to apply", False, COLOR_REMINDER)
            rem_x = self.panel.rect.right - 18 - rem_surf.get_width()
            surface.blit(rem_surf, (rem_x, self.panel.rect.y + 16))

        # Rows
        self.mode_selector.draw(surface)
        self.res_selector.draw(surface)
        self.fps_selector.draw(surface)
        self.toggle_vsync.draw(surface)
        self.toggle_show_fps.draw(surface)
        self.toggle_int_scale.draw(surface)

        # Footer Buttons
        self.btn_apply.draw(surface)
        self.btn_reset.draw(surface)
        self.btn_back.draw(surface)

        # Draw Restart Required Modal Overlay if active
        if self.modal_active:
            # Heavy darken curtain behind modal
            m_curtain = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            m_curtain.fill((0, 0, 0, 200))
            surface.blit(m_curtain, (0, 0))

            # Modal box
            modal_surf = pygame.Surface((self.modal_rect.width, self.modal_rect.height), pygame.SRCALPHA)
            modal_surf.fill(COLOR_PANEL_BG)
            pygame.draw.rect(modal_surf, COLOR_PANEL_BORDER, modal_surf.get_rect(), 1, border_radius=4)
            surface.blit(modal_surf, self.modal_rect.topleft)

            # Modal Title
            t_title = self.font.render("Restart required", False, COLOR_WHITE)
            surface.blit(t_title, t_title.get_rect(center=(self.modal_rect.centerx, self.modal_rect.y + 16)))

            # Message
            t_msg = self.font.render("Display changes need a restart to take effect.", False, (220, 220, 230))
            surface.blit(t_msg, t_msg.get_rect(center=(self.modal_rect.centerx, self.modal_rect.y + 36)))

            # Error message if restart failed
            if self.modal_error:
                t_err = self.font.render(self.modal_error, False, COLOR_ERROR)
                surface.blit(t_err, t_err.get_rect(center=(self.modal_rect.centerx, self.modal_rect.y + 53)))

            self.btn_restart_now.draw(surface)
            self.btn_later.draw(surface)
