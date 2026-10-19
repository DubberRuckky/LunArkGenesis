# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Display management: window creation, scaling, and coordinate conversion.

The game draws everything to a small internal canvas (480×270).
This module scales that canvas to fill the window while keeping
the aspect ratio and optionally using integer scaling.
"""

import logging
import math
import platform
from typing import List, Tuple

import pygame

from game.constants import (
    INTERNAL_WIDTH,
    INTERNAL_HEIGHT,
    AVAILABLE_RESOLUTIONS,
    DEFAULT_RESOLUTION,
)

logger = logging.getLogger("lunark.display")


# ---------------------------------------------------------------------------
# DPI awareness (Windows-only, called once before pygame.init)
# ---------------------------------------------------------------------------

def enable_dpi_awareness() -> None:
    """Enable DPI awareness on Windows so the OS reports true pixel sizes.

    Must be called *before* ``pygame.init()``.  On non-Windows platforms
    this is a harmless no-op.
    """
    if platform.system() != "Windows":
        return
    try:
        import ctypes  # noqa: WPS433 – conditional import is intentional
        ctypes.windll.user32.SetProcessDPIAware()
        logger.info("Windows DPI awareness enabled.")
    except Exception:
        # Not critical – the window may just be scaled by the OS compositor.
        logger.warning("Could not enable DPI awareness.", exc_info=True)


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def get_desktop_size() -> Tuple[int, int]:
    """Return the primary monitor resolution before a Display is created.

    Falls back to (1280, 720) if detection fails so the game never crashes.
    """
    try:
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            return (int(sizes[0][0]), int(sizes[0][1]))
    except Exception:
        logger.warning("get_desktop_sizes() unavailable, trying Info().")

    try:
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            return (int(info.current_w), int(info.current_h))
    except Exception:
        logger.warning("pygame.display.Info() failed.", exc_info=True)

    return (1280, 720)


# ---------------------------------------------------------------------------
# Display class
# ---------------------------------------------------------------------------

class Display:
    """Manages the OS window, internal canvas, and coordinate mapping.

    Attributes:
        window: The actual OS window surface.
        canvas: The internal 480×270 surface everything is drawn onto.
        settings: Reference to the current settings dictionary.
        scale_factor: Current canvas→window scale multiplier.
        offset: ``(x, y)`` pixel offset for letterbox bars.
        window_size: Current window dimensions in pixels.
        is_fullscreen: Whether the window is in fullscreen mode.
    """

    def __init__(self, settings: dict) -> None:
        """Initialise the display manager.

        Args:
            settings: Game settings dict (from ``logic/settings.py``).
        """
        self.settings: dict = settings
        # Plain Surface (no alpha) — the sky background is drawn first anyway.
        self.canvas: pygame.Surface = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT)
        )

        self.window: pygame.Surface = None  # type: ignore[assignment]
        self.scale_factor: float = 1.0
        self.offset: Tuple[int, int] = (0, 0)
        self.window_size: Tuple[int, int] = DEFAULT_RESOLUTION
        self.is_fullscreen: bool = settings.get("fullscreen", False)

        # Scaled destination rect – cached for render_canvas().
        self._scaled_rect: pygame.Rect = pygame.Rect(0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT)

        self.create_window()

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def create_window(self) -> None:
        """Create or recreate the pygame window based on current settings."""
        vsync_flag: int = 1 if self.settings.get("vsync", False) else 0
        desktop_w, desktop_h = self.get_desktop_resolution()

        if self.is_fullscreen:
            # NOFRAME gives a true borderless fullscreen that covers the
            # taskbar, which feels more polished than SCALED.
            self.window = pygame.display.set_mode(
                (desktop_w, desktop_h),
                pygame.FULLSCREEN | pygame.NOFRAME,
                vsync=vsync_flag,
            )
        else:
            res = self.settings.get("resolution", DEFAULT_RESOLUTION)
            target_w, target_h = int(res[0]), int(res[1])
            if target_w > desktop_w or target_h > desktop_h:
                logger.warning(
                    "Saved window size (%d, %d) exceeds desktop resolution (%d, %d). Shrinking window.",
                    target_w,
                    target_h,
                    desktop_w,
                    desktop_h,
                )
                def_w, def_h = DEFAULT_RESOLUTION
                if def_w <= desktop_w and def_h <= desktop_h:
                    target_w, target_h = def_w, def_h
                else:
                    target_w, target_h = desktop_w, desktop_h
                self.settings["resolution"] = [target_w, target_h]

            self.window = pygame.display.set_mode(
                (target_w, target_h),
                pygame.RESIZABLE,
                vsync=vsync_flag,
            )

        pygame.display.set_caption("LunArk: Genesis")
        self.window_size = self.window.get_size()
        self._calculate_scaling()
        logger.info(
            "Window created: %s  fullscreen=%s  vsync=%s",
            self.window_size, self.is_fullscreen, bool(vsync_flag),
        )

    def handle_resize(self, new_size: Tuple[int, int] | None = None) -> None:
        """Handle window resize event, refreshing surface and recalculating scaling.

        Args:
            new_size: Optional (w, h) tuple passed from VIDEORESIZE event.
        """
        surface = pygame.display.get_surface()
        if surface is not None:
            self.window = surface
            self.window_size = self.window.get_size()
        elif new_size:
            self.window_size = new_size
        self._calculate_scaling()

    def _calculate_scaling(self) -> None:
        """Calculate scale factor, offset, and cached scaled rect.

        Integer-scaling (when enabled) floors the multiplier so every
        source pixel maps to an exact NxN block — this avoids shimmering
        on pixel-art but may leave larger black bars.
        """
        win_w, win_h = self.window.get_size()
        self.window_size = (win_w, win_h)

        raw_scale: float = min(
            win_w / INTERNAL_WIDTH,
            win_h / INTERNAL_HEIGHT,
        )

        if self.settings.get("integer_scaling", False):
            # Floor to nearest integer, but never below 1×.
            self.scale_factor = float(max(1, math.floor(raw_scale)))
        else:
            self.scale_factor = raw_scale

        scaled_w: int = int(INTERNAL_WIDTH * self.scale_factor)
        scaled_h: int = int(INTERNAL_HEIGHT * self.scale_factor)

        # Centre the scaled image within the window (letterbox / pillarbox).
        offset_x: int = (win_w - scaled_w) // 2
        offset_y: int = (win_h - scaled_h) // 2
        self.offset = (offset_x, offset_y)

        self._scaled_rect = pygame.Rect(offset_x, offset_y, scaled_w, scaled_h)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_canvas(self) -> None:
        """Scale the internal canvas onto the window and flip the display."""
        # Black fill covers letterbox / pillarbox bars.
        self.window.fill((0, 0, 0))

        scaled = pygame.transform.scale(
            self.canvas,
            (self._scaled_rect.width, self._scaled_rect.height),
        )
        self.window.blit(scaled, self._scaled_rect.topleft)
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    def window_to_canvas(self, window_x: int, window_y: int) -> Tuple[int, int]:
        """Convert a window-space mouse position to canvas-space coordinates.

        Args:
            window_x: X position in window pixels.
            window_y: Y position in window pixels.

        Returns:
            ``(cx, cy)`` clamped to valid canvas pixel indices.
        """
        cx: int = int((window_x - self.offset[0]) / self.scale_factor)
        cy: int = int((window_y - self.offset[1]) / self.scale_factor)

        # Clamp to canvas bounds so callers never get out-of-range values.
        cx = max(0, min(cx, INTERNAL_WIDTH - 1))
        cy = max(0, min(cy, INTERNAL_HEIGHT - 1))
        return (cx, cy)

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------

    def toggle_fullscreen(self) -> None:
        """Toggle between fullscreen and windowed mode.

        We fully recreate the window instead of calling
        ``pygame.display.toggle_fullscreen()`` because the latter can
        leave artefacts or fail to resize correctly on some drivers —
        especially under Windows with mixed-DPI monitors.
        """
        self.is_fullscreen = not self.is_fullscreen
        self.settings["fullscreen"] = self.is_fullscreen
        self.create_window()

    def apply_settings(self, new_settings: dict) -> None:
        """Apply updated settings, recreating the window if needed.

        Args:
            new_settings: Dictionary of changed settings to merge in.
        """
        needs_recreate: bool = False

        for key in ("resolution", "fullscreen", "vsync", "integer_scaling"):
            if key in new_settings and new_settings[key] != self.settings.get(key):
                needs_recreate = True

        self.settings.update(new_settings)
        self.is_fullscreen = self.settings.get("fullscreen", False)

        if needs_recreate:
            self.create_window()
        else:
            # Recalc scaling in case the window was resized externally.
            self._calculate_scaling()

    def get_desktop_resolution(self) -> Tuple[int, int]:
        """Return the primary monitor's desktop resolution.

        Returns:
            ``(width, height)`` in physical pixels.
        """
        return get_desktop_size()

    def get_available_resolutions(self) -> List[Tuple[int, int]]:
        """Return resolutions from ``AVAILABLE_RESOLUTIONS`` that fit the desktop.

        The native desktop resolution is appended if not already present.
        The list is sorted ascending by total pixel count.

        Returns:
            Sorted list of ``(width, height)`` tuples.
        """
        desktop_w, desktop_h = self.get_desktop_resolution()

        valid: List[Tuple[int, int]] = [
            (w, h)
            for w, h in AVAILABLE_RESOLUTIONS
            if w <= desktop_w and h <= desktop_h
        ]

        native = (desktop_w, desktop_h)
        if native not in valid:
            valid.append(native)

        # Sort by total pixel count so the UI list goes small → large.
        valid.sort(key=lambda r: r[0] * r[1])
        return valid
