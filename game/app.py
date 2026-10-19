# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Application core and main loop for LunArk: Genesis.

Coordinates window lifecycle, screen stack management, frame timing,
fixed logic ticks, input event routing, and debug overlays.
"""

from copy import deepcopy
import logging
import subprocess
import sys
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_WHITE,
    DEFAULT_FPS,
    FONT_SIZE_SMALL,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    ROOT_DIR,
    SCREEN_SETTINGS,
    SCREEN_SPLASH,
    SCREEN_STARTUP,
    SCREEN_TITLE,
    STARTUP_ENABLED,
)
from game.logic.restart import build_restart_command
from game.logic.settings import (
    LIVE_KEYS,
    load_settings,
    needs_restart,
    save_settings,
)
from game.ui.display import Display, enable_dpi_awareness, get_desktop_size
from game.ui.screens.settings_menu import SettingsScreen
from game.ui.screens.startup import StartupScreen
from game.ui.screens.title import TitleScreen

# Configure basic console logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("lunark.app")


class App:
    """Central engine orchestrating the Pygame loop and state hierarchy."""

    def __init__(self, skip_startup: bool = False) -> None:
        # 1. Enable DPI awareness on Windows before display initialization
        enable_dpi_awareness()

        # 2. Initialize Pygame core & font subsystems
        pygame.init()
        pygame.font.init()

        # 3. Detect desktop resolution and load validated settings
        self.desktop_size = get_desktop_size()
        self.saved_settings: dict = load_settings(extra_resolutions=self.desktop_size)
        self.running_settings: dict = deepcopy(self.saved_settings)
        self.settings: dict = self.running_settings

        # 4. Create display adapter and window
        self.display = Display(self.running_settings)

        # 5. Preload assets
        assets.load_all()

        # 6. Screen Stack management
        # Screen stack allows modals (like Settings) to overlay previous screens
        self.screen_stack: list[object] = []
        self.screen_registry: dict[str, type] = {
            SCREEN_STARTUP: StartupScreen,
            SCREEN_SPLASH: StartupScreen,
            SCREEN_TITLE: TitleScreen,
            SCREEN_SETTINGS: SettingsScreen,
        }

        # Start with startup sequence if enabled and not skipped, otherwise straight to title screen
        if STARTUP_ENABLED and not skip_startup:
            self.set_screen(SCREEN_STARTUP)
        else:
            self.set_screen(SCREEN_TITLE)

        # Clock & frame tracking
        self.clock = pygame.time.Clock()
        self.running: bool = True
        self.fps_timer: float = 0.0
        self.current_fps: float = 0.0

        # Debug F3 overlay
        self.show_f3_debug: bool = False
        self.small_font = assets.get_font(FONT_SIZE_SMALL)

    # -----------------------------------------------------------------------
    # Screen Stack Methods
    # -----------------------------------------------------------------------

    def set_screen(self, screen_name: str) -> None:
        """Replace entire screen stack with a new instance of screen_name."""
        cls = self.screen_registry.get(screen_name)
        if cls:
            self.screen_stack = [cls(self)]
        else:
            logger.error("Attempted to switch to unregistered screen: %s", screen_name)

    def push_screen(self, screen_name: str) -> None:
        """Push a screen onto the stack (e.g. settings overlay)."""
        cls = self.screen_registry.get(screen_name)
        if cls:
            self.screen_stack.append(cls(self))
        else:
            logger.error("Attempted to push unregistered screen: %s", screen_name)

    def pop_screen(self) -> None:
        """Pop topmost screen from stack."""
        if len(self.screen_stack) > 1:
            self.screen_stack.pop()

    def get_current_screen(self) -> object | None:
        """Return active top-of-stack screen."""
        if self.screen_stack:
            return self.screen_stack[-1]
        return None

    # -----------------------------------------------------------------------
    # Coordinate Conversion & Input Helpers
    # -----------------------------------------------------------------------

    def get_canvas_mouse_pos(self) -> tuple[int, int]:
        """Convert current window mouse coordinates to 480x270 canvas pixels."""
        wx, wy = pygame.mouse.get_pos()
        return self.display.window_to_canvas(wx, wy)

    # -----------------------------------------------------------------------
    # Settings & Restart Application
    # -----------------------------------------------------------------------

    def is_restart_pending(self) -> bool:
        """Return True if any restart-needed setting differs between running and saved."""
        return needs_restart(self.running_settings, self.saved_settings)

    def apply_saved_settings(self, new_saved: dict) -> None:
        """Save new settings to disk and apply live settings immediately."""
        save_settings(new_saved, extra_resolutions=self.desktop_size)
        self.saved_settings = deepcopy(new_saved)

        # Apply live settings immediately to running session
        for k in LIVE_KEYS:
            if k in new_saved:
                self.running_settings[k] = new_saved[k]
        self.display.apply_settings(
            {k: self.running_settings[k] for k in LIVE_KEYS if k in self.running_settings}
        )

    def apply_settings(self, new_settings: dict, save_to_disk: bool = True) -> None:
        """Apply modified settings dictionary and update window/display adapter."""
        if save_to_disk:
            self.apply_saved_settings(new_settings)
        else:
            for k in LIVE_KEYS:
                if k in new_settings:
                    self.running_settings[k] = new_settings[k]
            self.display.apply_settings(new_settings)

    def restart_game(self) -> bool:
        """Start a new copy of the game and terminate the current process."""
        try:
            cmd = build_restart_command()
            logger.info("Restarting game with command: %s", cmd)
            subprocess.Popen(cmd, cwd=str(ROOT_DIR))
            self.quit_game()
            return True
        except Exception as exc:
            logger.error("Failed to launch restart process: %s", exc)
            return False

    def quit_game(self) -> None:
        """Initiate graceful application shutdown."""
        self.running = False

    # -----------------------------------------------------------------------
    # Main Game Loop
    # -----------------------------------------------------------------------

    def run(self) -> None:
        """Execute the primary game loop with delta-time updates and fixed rendering."""
        logger.info("LunArk: Genesis running. Internal canvas: %dx%d.", INTERNAL_WIDTH, INTERNAL_HEIGHT)

        while self.running:
            # 1. Delta time calculation (seconds)
            fps_cap = self.running_settings.get("fps_cap", DEFAULT_FPS)
            dt_ms = self.clock.tick(fps_cap) if fps_cap > 0 else self.clock.tick()
            dt = min(0.1, dt_ms / 1000.0)  # Clamp dt to prevent spiral of death on lag spikes

            self.current_fps = self.clock.get_fps()

            # 2. Event polling & global shortcuts
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit_game()

                elif event.type == pygame.VIDEORESIZE:
                    self.display.handle_resize(event.size)

                elif event.type == pygame.KEYDOWN:
                    # Global F11: Fullscreen toggle
                    if event.key == pygame.K_F11:
                        self.display.toggle_fullscreen()
                        self.running_settings["fullscreen"] = self.display.is_fullscreen
                        self.saved_settings["fullscreen"] = self.display.is_fullscreen
                        save_settings(self.saved_settings, extra_resolutions=self.desktop_size)

                    # Global F3: Debug placeholder overlay toggle
                    elif event.key == pygame.K_F3:
                        self.show_f3_debug = not self.show_f3_debug

            # 3. Route events to active top screen
            cur_screen = self.get_current_screen()
            if cur_screen and hasattr(cur_screen, "handle_events"):
                cur_screen.handle_events(events)

            # 4. Update active screen
            if cur_screen and hasattr(cur_screen, "update"):
                cur_screen.update(dt)

            # 5. Render active screen to 480x270 internal canvas
            self.display.canvas.fill(COLOR_BLACK)
            if cur_screen and hasattr(cur_screen, "draw"):
                cur_screen.draw(self.display.canvas)

            # 6. Render Overlays (FPS counter & F3 Debug)
            self._draw_overlays(self.display.canvas)

            # 7. Nearest-neighbor scale internal canvas to OS window & flip
            self.display.render_canvas()

        # Teardown
        pygame.quit()
        logger.info("Application closed cleanly.")
        sys.exit(0)

    def _draw_overlays(self, surface: pygame.Surface) -> None:
        """Render FPS counter and F3 missing-asset diagnostic banner."""
        # FPS Counter (top right)
        if self.running_settings.get("show_fps", False):
            fps_str = f"FPS: {int(self.current_fps + 0.5)}"
            txt = self.small_font.render(fps_str, False, (100, 255, 100))
            surface.blit(txt, (INTERNAL_WIDTH - txt.get_width() - 4, 4))

        # F3 Debug HUD
        if self.show_f3_debug:
            missing_list = assets.get_placeholder_list()
            item_h = 14
            max_items = 10
            num_shown = min(max_items, len(missing_list))
            total_rows = 1 + num_shown + (1 if len(missing_list) > max_items else 0)
            hud_h = 8 + total_rows * item_h
            overlay_surf = pygame.Surface((250, hud_h), pygame.SRCALPHA)
            overlay_surf.fill((10, 10, 20, 230))
            pygame.draw.rect(overlay_surf, (80, 180, 255), overlay_surf.get_rect(), 1)

            title = self.small_font.render(f"F3 DEBUG - Placeholders ({len(missing_list)})", False, (80, 180, 255))
            overlay_surf.blit(title, (4, 4))

            y = 4 + item_h
            for key in missing_list[:max_items]:
                item_txt = self.small_font.render(f"- {key}", False, COLOR_WHITE)
                overlay_surf.blit(item_txt, (6, y))
                y += item_h

            if len(missing_list) > max_items:
                more_txt = self.small_font.render(f"...and {len(missing_list) - max_items} more", False, (180, 180, 180))
                overlay_surf.blit(more_txt, (6, y))

            surface.blit(overlay_surf, (4, 4))
