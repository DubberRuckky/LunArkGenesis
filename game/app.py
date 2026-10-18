# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Application core and main loop for LunArk: Genesis.

Coordinates window lifecycle, screen stack management, frame timing,
fixed logic ticks, input event routing, and debug overlays.
"""

import logging
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
    SCREEN_SETTINGS,
    SCREEN_SPLASH,
    SCREEN_TITLE,
)
from game.logic.settings import load_settings, save_settings
from game.ui.display import Display, enable_dpi_awareness
from game.ui.screens.settings_menu import SettingsScreen
from game.ui.screens.splash import SplashScreen
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

    def __init__(self) -> None:
        # 1. Enable DPI awareness on Windows before display initialization
        enable_dpi_awareness()

        # 2. Initialize Pygame core & font subsystems
        pygame.init()
        pygame.font.init()

        # 3. Load validated settings
        self.settings: dict = load_settings()

        # 4. Create display adapter and window
        self.display = Display(self.settings)

        # 5. Preload assets
        assets.load_all()

        # 6. Screen Stack management
        # Screen stack allows modals (like Settings) to overlay previous screens
        self.screen_stack: list[object] = []
        self.screen_registry: dict[str, type] = {
            SCREEN_SPLASH: SplashScreen,
            SCREEN_TITLE: TitleScreen,
            SCREEN_SETTINGS: SettingsScreen,
        }

        # Start with splash screen
        self.set_screen(SCREEN_SPLASH)

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
    # Settings Application
    # -----------------------------------------------------------------------

    def apply_settings(self, new_settings: dict, save_to_disk: bool = True) -> None:
        """Apply modified settings dictionary and update window/display adapter."""
        self.settings.update(new_settings)
        self.display.apply_settings(new_settings)
        if save_to_disk:
            save_settings(self.settings)

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
            fps_cap = self.settings.get("fps_cap", DEFAULT_FPS)
            dt_ms = self.clock.tick(fps_cap) if fps_cap > 0 else self.clock.tick()
            dt = min(0.1, dt_ms / 1000.0)  # Clamp dt to prevent spiral of death on lag spikes

            self.current_fps = self.clock.get_fps()

            # 2. Event polling & global shortcuts
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit_game()

                elif event.type == pygame.KEYDOWN:
                    # Global F11: Fullscreen toggle
                    if event.key == pygame.K_F11:
                        self.display.toggle_fullscreen()
                        self.settings["fullscreen"] = self.display.is_fullscreen
                        save_settings(self.settings)

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
        if self.settings.get("show_fps", False):
            fps_str = f"FPS: {int(self.current_fps + 0.5)}"
            txt = self.small_font.render(fps_str, False, (100, 255, 100))
            surface.blit(txt, (INTERNAL_WIDTH - txt.get_width() - 4, 4))

        # F3 Debug HUD
        if self.show_f3_debug:
            missing_list = assets.get_placeholder_list()
            hud_h = min(120, 16 + len(missing_list) * 10)
            overlay_surf = pygame.Surface((220, hud_h), pygame.SRCALPHA)
            overlay_surf.fill((10, 10, 20, 230))
            pygame.draw.rect(overlay_surf, (80, 180, 255), overlay_surf.get_rect(), 1)

            title = self.small_font.render(f"F3 DEBUG - Placeholders ({len(missing_list)})", False, (80, 180, 255))
            overlay_surf.blit(title, (4, 4))

            y = 16
            for key in missing_list[:10]:
                item_txt = self.small_font.render(f"- {key}", False, COLOR_WHITE)
                overlay_surf.blit(item_txt, (6, y))
                y += 10

            if len(missing_list) > 10:
                more_txt = self.small_font.render(f"...and {len(missing_list) - 10} more", False, (180, 180, 180))
                overlay_surf.blit(more_txt, (6, y))

            surface.blit(overlay_surf, (4, 4))
