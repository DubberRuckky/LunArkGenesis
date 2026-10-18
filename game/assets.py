# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Asset manager for LunArk: Genesis.

Handles image loading, placeholder fallback generation, 9-slice UI scaling,
sprite-strip slicing, and font loading. When art is missing, a labelled
placeholder is generated at runtime and logged once.
"""

from collections.abc import Callable
import logging
from pathlib import Path

import pygame

from game.constants import (
    ASSET_PATHS,
    COLOR_BLACK,
    COLOR_PLACEHOLDER,
    COLOR_PLACEHOLDER_TEXT,
    FONT_DIR,
    FONT_NAME,
    FONT_SIZE_MEDIUM,
    IMG_DIR,
)

logger = logging.getLogger("lunark.assets")


def create_placeholder(width: int, height: int, label: str) -> pygame.Surface:
    """Create a labelled magenta placeholder surface for missing art.

    Args:
        width: Surface width in pixels.
        height: Surface height in pixels.
        label: Text to render inside the placeholder.

    Returns:
        pygame.Surface: Colored surface with centered text label.
    """
    surf = pygame.Surface((max(16, width), max(16, height)), pygame.SRCALPHA)
    surf.fill(COLOR_PLACEHOLDER)

    # Inner border for visual definition
    pygame.draw.rect(surf, (220, 100, 220), surf.get_rect(), 1)

    try:
        font = pygame.font.Font(None, 12)
        text_surf = font.render(label[:16], False, COLOR_PLACEHOLDER_TEXT)
        rect = text_surf.get_rect(center=(surf.get_width() // 2, surf.get_height() // 2))
        surf.blit(text_surf, rect)
    except Exception:
        # Fallback if font subsystem not yet ready
        pass

    return surf


def load_sprite_strip(
    surface: pygame.Surface,
    frame_width: int,
    frame_height: int,
) -> list[pygame.Surface]:
    """Slice a horizontal sprite strip into individual animation frames.

    Frame count is automatically detected from image_width // frame_width.

    Args:
        surface: Source sprite strip surface.
        frame_width: Width of each frame in pixels.
        frame_height: Height of each frame in pixels.

    Returns:
        list[pygame.Surface]: List of extracted sub-surfaces.
    """
    if frame_width <= 0 or frame_height <= 0:
        return [surface]

    frames_count = max(1, surface.get_width() // frame_width)
    frames: list[pygame.Surface] = []
    for i in range(frames_count):
        rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        frame = surface.subsurface(rect).copy()
        frames.append(frame)
    return frames


def make_nine_slice(
    surface: pygame.Surface,
    corner: int,
) -> Callable[[pygame.Surface, pygame.Rect], None]:
    """Create a 9-slice rendering function for scalable UI panels and buttons.

    The 9-slice separates corners (unscaled) from edges and center (scaled
    with nearest-neighbor to maintain crisp pixel art).

    Args:
        surface: Source UI slice texture.
        corner: Width and height of the corner segments in pixels.

    Returns:
        Callable[[pygame.Surface, pygame.Rect], None]: Drawing function.
    """
    sw, sh = surface.get_width(), surface.get_height()
    c = corner

    # Pre-extract the 9 regions
    c_w = min(c, sw // 2)
    c_h = min(c, sh // 2)
    mid_w = sw - 2 * c_w
    mid_h = sh - 2 * c_h

    tl = surface.subsurface(pygame.Rect(0, 0, c_w, c_h))
    tr = surface.subsurface(pygame.Rect(sw - c_w, 0, c_w, c_h))
    bl = surface.subsurface(pygame.Rect(0, sh - c_h, c_w, c_h))
    br = surface.subsurface(pygame.Rect(sw - c_w, sh - c_h, c_w, c_h))

    t_edge = surface.subsurface(pygame.Rect(c_w, 0, mid_w, c_h)) if mid_w > 0 else None
    b_edge = surface.subsurface(pygame.Rect(c_w, sh - c_h, mid_w, c_h)) if mid_w > 0 else None
    l_edge = surface.subsurface(pygame.Rect(0, c_h, c_w, mid_h)) if mid_h > 0 else None
    r_edge = surface.subsurface(pygame.Rect(sw - c_w, c_h, c_w, mid_h)) if mid_h > 0 else None
    center = surface.subsurface(pygame.Rect(c_w, c_h, mid_w, mid_h)) if (mid_w > 0 and mid_h > 0) else None

    def draw_slice(target: pygame.Surface, dest_rect: pygame.Rect) -> None:
        dw, dh = dest_rect.width, dest_rect.height
        dx, dy = dest_rect.x, dest_rect.y

        # Scale center and edges if destination is larger than corners
        mid_dw = max(0, dw - 2 * c_w)
        mid_dh = max(0, dh - 2 * c_h)

        # 1. Center
        if center and mid_dw > 0 and mid_dh > 0:
            scaled_center = pygame.transform.scale(center, (mid_dw, mid_dh))
            target.blit(scaled_center, (dx + c_w, dy + c_h))

        # 2. Edges
        if t_edge and mid_dw > 0:
            target.blit(pygame.transform.scale(t_edge, (mid_dw, c_h)), (dx + c_w, dy))
        if b_edge and mid_dw > 0:
            target.blit(pygame.transform.scale(b_edge, (mid_dw, c_h)), (dx + c_w, dy + dh - c_h))
        if l_edge and mid_dh > 0:
            target.blit(pygame.transform.scale(l_edge, (c_w, mid_dh)), (dx, dy + c_h))
        if r_edge and mid_dh > 0:
            target.blit(pygame.transform.scale(r_edge, (c_w, mid_dh)), (dx + dw - c_w, dy + c_h))

        # 3. Corners
        target.blit(tl, (dx, dy))
        target.blit(tr, (dx + dw - c_w, dy))
        target.blit(bl, (dx, dy + dh - c_h))
        target.blit(br, (dx + dw - c_w, dy + dh - c_h))

    return draw_slice


class AssetManager:
    """Singleton repository managing image, font, and UI slice resources.

    Ensures missing assets never cause crashes by providing immediate
    procedural replacements.
    """

    def __init__(self) -> None:
        self.images: dict[str, pygame.Surface] = {}
        self.fonts: dict[int, pygame.font.Font] = {}
        self.missing: set[str] = set()
        self.slices: dict[str, Callable[[pygame.Surface, pygame.Rect], None]] = {}

    def get_font(self, size: int = FONT_SIZE_MEDIUM) -> pygame.font.Font:
        """Fetch or load a font at the requested size with default fallback.

        Args:
            size: Font size in points.

        Returns:
            pygame.font.Font: Loaded TTF or Pygame system default font.
        """
        if size in self.fonts:
            return self.fonts[size]

        font_path = FONT_DIR / FONT_NAME
        if font_path.exists():
            try:
                font = pygame.font.Font(str(font_path), size)
                self.fonts[size] = font
                return font
            except Exception as exc:
                logger.warning("Failed to load font from %s: %s. Using default font.", font_path, exc)

        # Pygame default font
        font = pygame.font.Font(None, size)
        self.fonts[size] = font
        return font

    def load_image(self, key: str, default_size: tuple[int, int] = (32, 32)) -> pygame.Surface:
        """Load an image by asset key from ASSET_PATHS, with placeholder fallback.

        Args:
            key: Lookup key defined in constants.ASSET_PATHS.
            default_size: Dimensions used when creating a placeholder.

        Returns:
            pygame.Surface: Alpha-converted Pygame surface.
        """
        if key in self.images:
            return self.images[key]

        rel_path = ASSET_PATHS.get(key)
        if not rel_path:
            logger.warning("Unregistered asset key requested: %s", key)
            surf = create_placeholder(default_size[0], default_size[1], key)
            self.images[key] = surf
            self.missing.add(key)
            return surf

        abs_path = IMG_DIR / rel_path
        if abs_path.exists():
            try:
                raw_surf = pygame.image.load(str(abs_path))
                # Convert with alpha if display is initialized
                if pygame.display.get_surface() is not None:
                    surf = raw_surf.convert_alpha()
                else:
                    surf = raw_surf
                self.images[key] = surf
                return surf
            except Exception as exc:
                logger.warning("Failed loading image %s: %s. Using placeholder.", abs_path, exc)

        # Missing or failed load: construct placeholder
        self.missing.add(key)
        logger.warning("Asset not found on disk: %s (Key: '%s'). Fallback generated.", abs_path, key)
        surf = create_placeholder(default_size[0], default_size[1], key)
        self.images[key] = surf
        return surf

    def load_all(self) -> None:
        """Preload all registered asset paths and initialize UI slice helpers."""
        # Expected dimensions for key placeholders when files are absent
        known_sizes: dict[str, tuple[int, int]] = {
            "logo": (33, 33),
            "title": (240, 60),
            "title_bg": (480, 270),
            "panel": (24, 24),
            "button": (96, 24),
            "bar_frame": (12, 10),
            "dialogue_box": (24, 24),
            "toggle": (48, 12),
            "next_arrow": (16, 8),
            "cursor": (32, 16),
            "icons": (128, 48),
            "tileset": (128, 48),
            "mentor": (256, 64),
            "wake_up_1": (480, 270),
        }

        for key in ASSET_PATHS:
            size = known_sizes.get(key, (32, 32))
            self.load_image(key, default_size=size)

        self.print_missing_summary()

    def print_missing_summary(self) -> None:
        """Print a concise console summary of missing assets at game startup."""
        if self.missing:
            logger.info("=== Asset Summary: %d missing asset(s) using placeholders ===", len(self.missing))
            for key in sorted(self.missing):
                rel = ASSET_PATHS.get(key, "unknown")
                logger.info("  [-] %s -> img/%s", key, rel)
            logger.info("Drop corresponding .png files into img/ to replace placeholders automatically.")
        else:
            logger.info("All registered assets loaded successfully!")

    def get_placeholder_list(self) -> list[str]:
        """Return the list of current placeholder asset keys for F3 debug view.

        Returns:
            list[str]: Sorted list of missing asset keys.
        """
        return sorted(list(self.missing))


# Global singleton instance
assets = AssetManager()
