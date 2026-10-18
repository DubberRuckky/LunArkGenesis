# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Settings menu screen with auto-revert display confirmation.

Allows tuning display mode, resolution, FPS cap, VSync, integer scaling,
and performance metrics, protecting players with a 10s safety revert countdown.
"""

from copy import deepcopy
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_WHITE,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FPS_OPTIONS,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SETTINGS_REVERT_SECONDS,
)
from game.logic.settings import (
    get_defaults,
    needs_display_change,
    save_settings,
    settings_changed,
    validate_settings,
)
from game.ui.widgets import Button, OptionSelector, Panel, Toggle


class SettingsScreen:
    """Full settings interface with video, display, and rendering options."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.header_font = assets.get_font(FONT_SIZE_LARGE)

        # Working copy of settings
        self.current_settings = deepcopy(self.app.settings)  # type: ignore[attr-defined]
        self.pending_settings = deepcopy(self.current_settings)

        # Revert confirmation modal state
        self.reverting_active: bool = False
        self.revert_timer: float = float(SETTINGS_REVERT_SECONDS)
        self.backup_settings: dict | None = None

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

        # Revert confirmation modal buttons
        modal_w = 260
        modal_h = 100
        modal_x = (INTERNAL_WIDTH - modal_w) // 2
        modal_y = (INTERNAL_HEIGHT - modal_h) // 2
        self.modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        self.btn_keep = Button(
            modal_x + 24,
            modal_y + 64,
            80,
            18,
            "Keep",
            self.font,
            callback=self._confirm_keep,
        )
        self.btn_revert = Button(
            modal_x + modal_w - 94 - 24,
            modal_y + 64,
            94,
            18,
            "Revert Now",
            self.font,
            callback=self._confirm_revert,
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
        self.mode_selector.set_index(0 if defaults["fullscreen"] else 1)
        self.res_selector.set_enabled(not defaults["fullscreen"])

        cur_res = tuple(defaults["resolution"])
        if cur_res in self.res_tuples:
            self.res_selector.set_index(self.res_tuples.index(cur_res))

        cur_fps = defaults["fps_cap"]
        if cur_fps in self.fps_values:
            self.fps_selector.set_index(self.fps_values.index(cur_fps))

        self.toggle_vsync.value = defaults["vsync"]
        self.toggle_show_fps.value = defaults["show_fps"]
        self.toggle_int_scale.value = defaults["integer_scaling"]

    def _on_apply(self) -> None:
        """Apply changes. Triggers auto-revert modal if display mode changed."""
        cleaned = validate_settings(self.pending_settings, self.res_tuples)
        self.pending_settings = cleaned

        if settings_changed(self.current_settings, self.pending_settings):
            # Display mode/resolution/scaling changed -> engage confirmation timer
            self.backup_settings = deepcopy(self.current_settings)
            self.revert_timer = float(SETTINGS_REVERT_SECONDS)
            self.reverting_active = True

            # Apply test mode to window
            self.app.apply_settings(self.pending_settings, save_to_disk=False)  # type: ignore[attr-defined]
            self.current_settings = deepcopy(self.pending_settings)
        else:
            # Only non-display settings changed (FPS cap, Show FPS, etc.)
            self.current_settings = deepcopy(self.pending_settings)
            self.app.apply_settings(self.current_settings, save_to_disk=True)  # type: ignore[attr-defined]

    def _confirm_keep(self) -> None:
        """User clicked Keep: save settings permanently and dismiss modal."""
        self.reverting_active = False
        save_settings(self.current_settings)
        self.backup_settings = None

    def _confirm_revert(self) -> None:
        """Revert window to previous backup settings."""
        self.reverting_active = False
        if self.backup_settings:
            self.current_settings = deepcopy(self.backup_settings)
            self.pending_settings = deepcopy(self.backup_settings)
            self.app.apply_settings(self.current_settings, save_to_disk=True)  # type: ignore[attr-defined]
            self._sync_widgets_from_settings(self.current_settings)
            self.backup_settings = None

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
        if self.reverting_active:
            self._confirm_revert()
        self.app.pop_screen()  # type: ignore[attr-defined]

    # -----------------------------------------------------------------------
    # Event & Update Loop
    # -----------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Route input events to modal or main settings controls."""
        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]

        # Handle ESC key: go back
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._on_back()
                return

        if self.reverting_active:
            self.btn_keep.update(events, mouse_pos)
            self.btn_revert.update(events, mouse_pos)
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
        """Tick auto-revert safety countdown."""
        if self.reverting_active:
            self.revert_timer -= dt
            if self.revert_timer <= 0.0:
                self._confirm_revert()

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

        # Draw Confirmation Modal Overlay if active
        if self.reverting_active:
            # Heavy darken curtain behind modal
            m_curtain = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            m_curtain.fill((0, 0, 0, 200))
            surface.blit(m_curtain, (0, 0))

            # Modal box
            modal_surf = pygame.Surface((self.modal_rect.width, self.modal_rect.height), pygame.SRCALPHA)
            modal_surf.fill(COLOR_PANEL_BG)
            pygame.draw.rect(modal_surf, COLOR_PANEL_BORDER, modal_surf.get_rect(), 1, border_radius=4)
            surface.blit(modal_surf, self.modal_rect.topleft)

            # Warning text & countdown
            msg_1 = "Keep these display settings?"
            msg_2 = f"Reverting in {max(0, int(self.revert_timer + 0.9))}s..."
            t1 = self.font.render(msg_1, False, COLOR_WHITE)
            t2 = self.font.render(msg_2, False, (255, 200, 80))
            surface.blit(t1, t1.get_rect(center=(self.modal_rect.centerx, self.modal_rect.y + 20)))
            surface.blit(t2, t2.get_rect(center=(self.modal_rect.centerx, self.modal_rect.y + 40)))

            self.btn_keep.draw(surface)
            self.btn_revert.draw(surface)
