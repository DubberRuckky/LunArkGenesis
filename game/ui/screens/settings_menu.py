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
from game.ui.widgets import (
    Button,
    OptionSelector,
    Panel,
    Toggle,
    draw_text,
    wrap_text,
    wrap_text_to_width,
)


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

        # Container panel layout (initialized at dummy size, sized in resize())
        self.panel = Panel(0, 0, 10, 10)
        self.col1_x: int = 0
        self.col2_x: int = 0
        self.col_w: int = 0

        # 1. Display mode selector
        self.mode_selector = OptionSelector(
            0,
            0,
            100,
            "Display Mode",
            ["Fullscreen", "Windowed"],
            self.font,
            selected_index=0 if self.pending_settings.get("fullscreen") else 1,
            callback=self._on_mode_changed,
        )

        # 2. Resolution selector
        self.res_selector = OptionSelector(
            0,
            0,
            100,
            "Resolution",
            self.res_strings,
            self.font,
            selected_index=res_idx,
            callback=self._on_res_changed,
            enabled=not self.pending_settings.get("fullscreen"),
        )

        # 3. FPS Cap selector
        self.fps_selector = OptionSelector(
            0,
            0,
            100,
            "FPS Cap",
            self.fps_strings,
            self.font,
            selected_index=fps_idx,
            callback=self._on_fps_changed,
        )

        # 4. VSync toggle
        self.toggle_vsync = Toggle(
            0,
            0,
            "VSync (Smooth Video)",
            self.font,
            value=self.pending_settings.get("vsync", True),
            callback=self._on_vsync_changed,
        )

        # 5. Integer scaling toggle
        self.toggle_int_scale = Toggle(
            0,
            0,
            "Integer Scaling (Sharp)",
            self.font,
            value=self.pending_settings.get("integer_scaling", True),
            callback=self._on_int_scale_changed,
        )

        # 6. Show FPS toggle
        self.toggle_show_fps = Toggle(
            0,
            0,
            "Show FPS Counter",
            self.font,
            value=self.pending_settings.get("show_fps", False),
            callback=self._on_show_fps_changed,
        )

        # Audio volume values: 0-10 displayed as 0%-100%
        vol_opts = [str(v * 10) + "%" for v in range(11)]

        # 7. Master volume
        self.audio_master_sel = OptionSelector(
            0,
            0,
            100,
            "Master Volume",
            vol_opts,
            self.font,
            selected_index=self.pending_settings.get("audio_master", 8),
            callback=lambda idx, _t: self._on_audio_changed("audio_master", idx),
        )

        # 8. Music volume
        self.audio_music_sel = OptionSelector(
            0,
            0,
            100,
            "Music Volume",
            vol_opts,
            self.font,
            selected_index=self.pending_settings.get("audio_music", 7),
            callback=lambda idx, _t: self._on_audio_changed("audio_music", idx),
        )

        # 9. Sound effects volume
        self.audio_sfx_sel = OptionSelector(
            0,
            0,
            100,
            "Effects Volume",
            vol_opts,
            self.font,
            selected_index=self.pending_settings.get("audio_sfx", 8),
            callback=lambda idx, _t: self._on_audio_changed("audio_sfx", idx),
        )

        # Action buttons
        self.btn_apply = Button(0, 0, 60, 18, "Apply", self.font, callback=self._on_apply)
        self.btn_reset = Button(0, 0, 114, 18, "Reset Defaults", self.font, callback=self._on_reset)
        self.btn_back = Button(0, 0, 60, 18, "Back", self.font, callback=self._on_back)

        # Restart modal
        self.modal_rect = pygame.Rect(0, 0, 10, 10)
        self.btn_restart_now = Button(0, 0, 100, 20, "Restart Now", self.font, callback=self._on_restart_now)
        self.btn_later = Button(0, 0, 64, 20, "Later", self.font, callback=self._on_later)

        self.buttons = [
            self.btn_apply,
            self.btn_reset,
            self.btn_back,
            self.btn_restart_now,
            self.btn_later,
        ]

        # Apply two-column screen-fitted layout
        self.resize(INTERNAL_WIDTH, INTERNAL_HEIGHT)

    def resize(self, width: int | None = None, height: int | None = None) -> None:
        """Dynamically center and scale the menu and controls to fit the screen properly."""
        w = int(width if width is not None else INTERNAL_WIDTH)
        h = int(height if height is not None else INTERNAL_HEIGHT)

        # Container panel fits neatly on screen with margin
        panel_w = min(452, w - 20)
        panel_h = min(244, h - 16)
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        self.panel.set_rect(panel_x, panel_y, panel_w, panel_h)

        interior_w = panel_w - 28
        col_gap = 14
        col_w = (interior_w - col_gap) // 2
        self.col1_x = panel_x + 14
        self.col2_x = self.col1_x + col_w + col_gap
        self.col_w = col_w

        start_y = panel_y + 44
        step_y = 25

        # Left column (Display & Video)
        self.mode_selector.set_position(self.col1_x, start_y, col_w)
        self.res_selector.set_position(self.col1_x, start_y + step_y, col_w)
        self.fps_selector.set_position(self.col1_x, start_y + step_y * 2, col_w)
        self.toggle_vsync.set_position(self.col1_x, start_y + step_y * 3)
        self.toggle_int_scale.set_position(self.col1_x, start_y + step_y * 4)
        self.toggle_show_fps.set_position(self.col1_x, start_y + step_y * 5)

        # Right column (Audio & Sound)
        self.audio_master_sel.set_position(self.col2_x, start_y, col_w)
        self.audio_music_sel.set_position(self.col2_x, start_y + step_y, col_w)
        self.audio_sfx_sel.set_position(self.col2_x, start_y + step_y * 2, col_w)

        # Action Buttons
        btn_y = panel_y + panel_h - 25
        btn_h = 18
        self.btn_apply.set_position(panel_x + 14, btn_y, 60, btn_h)
        self.btn_reset.set_position(panel_x + 82, btn_y, 114, btn_h)
        self.btn_back.set_position(panel_x + panel_w - 74, btn_y, 60, btn_h)

        # Modal
        modal_w = min(350, w - 40)
        modal_h = 104
        modal_x = (w - modal_w) // 2
        modal_y = (h - modal_h) // 2
        self.modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        btn_restart_w = 100
        btn_later_w = 64
        btn_gap = 16
        total_btn_w = btn_restart_w + btn_gap + btn_later_w
        modal_btn_x = modal_x + (modal_w - total_btn_w) // 2
        modal_btn_y = modal_y + 70
        self.btn_restart_now.set_position(modal_btn_x, modal_btn_y, btn_restart_w, 20)
        self.btn_later.set_position(modal_btn_x + btn_restart_w + btn_gap, modal_btn_y, btn_later_w, 20)

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

    def _on_audio_changed(self, key: str, idx: int) -> None:
        """Store audio volume level (0-10 steps)."""
        self.pending_settings[key] = idx

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
        self.audio_master_sel.set_index(st.get("audio_master", 8))
        self.audio_music_sel.set_index(st.get("audio_music", 7))
        self.audio_sfx_sel.set_index(st.get("audio_sfx", 8))

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
        self.audio_master_sel.update(events, mouse_pos)
        self.audio_music_sel.update(events, mouse_pos)
        self.audio_sfx_sel.update(events, mouse_pos)

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

        # Panel frame (centered on screen, guaranteed inside 480x270 bounds)
        self.panel.draw(surface)

        # Header Title
        title_surf = self.header_font.render("Settings", False, COLOR_WHITE)
        surface.blit(title_surf, (self.panel.rect.x + 16, self.panel.rect.y + 8))

        # Orange restart reminder in header if restart is pending
        if self.app.is_restart_pending():  # type: ignore[attr-defined]
            rem_surf = self.font.render("Restart to apply", False, COLOR_REMINDER)
            rem_x = self.panel.rect.right - 16 - rem_surf.get_width()
            surface.blit(rem_surf, (rem_x, self.panel.rect.y + 12))

        # Column Section Subheaders
        disp_hdr = self.font.render("Display & Video", False, (120, 190, 255))
        surface.blit(disp_hdr, (self.col1_x, self.panel.rect.y + 28))

        audio_hdr = self.font.render("Audio & Sound", False, (120, 190, 255))
        surface.blit(audio_hdr, (self.col2_x, self.panel.rect.y + 28))

        # Left Column Rows
        self.mode_selector.draw(surface)
        self.res_selector.draw(surface)
        self.fps_selector.draw(surface)
        self.toggle_vsync.draw(surface)
        self.toggle_int_scale.draw(surface)
        self.toggle_show_fps.draw(surface)

        # Right Column Rows
        self.audio_master_sel.draw(surface)
        self.audio_music_sel.draw(surface)
        self.audio_sfx_sel.draw(surface)

        # Cadet Controls Quick Tips Box in Right Column (Age 7-12 friendly)
        tips_y = self.panel.rect.y + 44 + 25 * 3 + 4
        tips_hdr = self.font.render("Cadet Controls:", False, (255, 215, 80))
        surface.blit(tips_hdr, (self.col2_x, tips_y))

        tip1 = self.font.render("* F11: Fullscreen toggle", False, (190, 195, 210))
        tip2 = self.font.render("* Space: Pause game", False, (190, 195, 210))
        tip3 = self.font.render("* ? or /: Controls guide", False, (190, 195, 210))
        surface.blit(tip1, (self.col2_x, tips_y + 15))
        surface.blit(tip2, (self.col2_x, tips_y + 28))
        surface.blit(tip3, (self.col2_x, tips_y + 41))

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


# Alias for backward compatibility and alternate naming
SettingsMenu = SettingsScreen
__all__ = ["SettingsScreen", "SettingsMenu"]
