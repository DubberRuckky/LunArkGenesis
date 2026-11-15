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


FRAME_ASSETS = {"bar_frame", "panel", "button", "dialogue_box", "toggle"}


def create_placeholder(width: int, height: int, label: str) -> pygame.Surface:
    """Create a labelled magenta placeholder or transparent-middle outline for frame assets.

    Frame assets (bar_frame, panel, button, dialogue_box, toggle) get an outline
    with an entirely transparent middle so underlying fills remain visible.

    Args:
        width: Surface width in pixels.
        height: Surface height in pixels.
        label: Asset identifier key.

    Returns:
        pygame.Surface: Transparent-middle outline for frames, or magenta box with text label.
    """
    w = max(1, width)
    h = max(1, height)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    if label in FRAME_ASSETS:
        surf.fill((0, 0, 0, 0))  # Transparent middle
        if label == "bar_frame":
            # 12x10 bar frame with 3px corner: 1px outline, transparent center
            pygame.draw.rect(surf, (140, 145, 165, 255), (0, 0, w, h), 1)
        elif label == "button":
            # 96x24: 4 states of 24x24 (normal, hover, pressed, disabled)
            state_w = w // 4 if w >= 4 else w
            border_cols = [
                (110, 115, 130, 255),  # normal
                (170, 175, 195, 255),  # hover
                (255, 220, 50, 255),   # pressed
                (70, 70, 80, 255),     # disabled
            ]
            for i in range(4):
                col = border_cols[i] if i < len(border_cols) else (120, 120, 120, 255)
                r = pygame.Rect(i * state_w, 0, state_w, h)
                pygame.draw.rect(surf, col, r, 2)
        elif label == "toggle":
            # 48x12: 2 states of 24x12 (off, on)
            half_w = w // 2
            pygame.draw.rect(surf, (90, 95, 110, 255), (0, 0, half_w, h), 1)
            pygame.draw.rect(surf, (100, 150, 240, 255), (half_w, 0, half_w, h), 1)
            pygame.draw.circle(surf, (150, 155, 170, 255), (4, h // 2), 3)
            pygame.draw.circle(surf, (255, 255, 255, 255), (half_w + half_w - 4, h // 2), 3)
        elif label == "dialogue_box":
            pygame.draw.rect(surf, (90, 110, 145, 255), (0, 0, w, h), 2)
        else:  # panel
            pygame.draw.rect(surf, (100, 105, 130, 255), (0, 0, w, h), 2)
        return surf

    # Non-frame placeholder: magenta box with label
    surf = pygame.Surface((max(16, w), max(16, h)), pygame.SRCALPHA)
    surf.fill(COLOR_PLACEHOLDER)
    pygame.draw.rect(surf, (220, 100, 220), surf.get_rect(), 1)
    try:
        font = pygame.font.Font(None, 12)
        text_surf = font.render(label[:16], False, COLOR_PLACEHOLDER_TEXT)
        rect = text_surf.get_rect(center=(surf.get_width() // 2, surf.get_height() // 2))
        surf.blit(text_surf, rect)
    except Exception:
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

                # Scale/crop high-res exports in Pygame to fit target canvas without modifying source files on disk
                if key == "logo" and (surf.get_width() > 99 or surf.get_height() > 99):
                    surf = pygame.transform.scale(surf, (33, 33))
                elif key == "logo_aseprite" and (surf.get_width() > 120 or surf.get_height() > 72):
                    scale = min(120 / surf.get_width(), 72 / surf.get_height())
                    surf = pygame.transform.smoothscale(
                        surf, (max(1, int(surf.get_width() * scale)), max(1, int(surf.get_height() * scale)))
                    )
                elif key == "logo_pygame_ce" and (surf.get_width() > 120 or surf.get_height() > 72):
                    scale = min(120 / surf.get_width(), 72 / surf.get_height())
                    surf = pygame.transform.smoothscale(
                        surf, (max(1, int(surf.get_width() * scale)), max(1, int(surf.get_height() * scale)))
                    )

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
            "logo_aseprite": (120, 72),
            "logo_pygame_ce": (120, 72),
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

        self.init_cursor()
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

    def get_icon(self, index: int) -> pygame.Surface:
        """Extract a 16x16 icon from the shared icon spritesheet by index."""
        sheet = self.load_image("icons", default_size=(128, 48))
        cols = 8
        row = index // cols
        col = index % cols
        x = col * 16
        y = row * 16
        if 0 <= x + 16 <= sheet.get_width() and 0 <= y + 16 <= sheet.get_height():
            return sheet.subsurface(pygame.Rect(x, y, 16, 16))
        return create_placeholder(16, 16, f"i{index}")

    def get_tile(self, index: int) -> pygame.Surface:
        """Extract a 16x16 terrain tile from the tileset spritesheet by index."""
        sheet = self.load_image("tileset", default_size=(128, 48))
        cols = 8
        row = index // cols
        col = index % cols
        x = col * 16
        y = row * 16
        if 0 <= x + 16 <= sheet.get_width() and 0 <= y + 16 <= sheet.get_height():
            return sheet.subsurface(pygame.Rect(x, y, 16, 16))
        return create_placeholder(16, 16, f"t{index}")

    def get_button_slices(self) -> list[Callable[[pygame.Surface, pygame.Rect], None]]:
        """Return list of four 9-slice functions for normal, hover, pressed, disabled states."""
        if hasattr(self, "_button_slices") and self._button_slices:
            return self._button_slices

        btn_sheet = self.load_image("button", default_size=(96, 24))
        slices: list[Callable[[pygame.Surface, pygame.Rect], None]] = []
        state_w = 24
        corner = 8
        for i in range(4):
            x = i * state_w
            if x + state_w <= btn_sheet.get_width():
                sub = btn_sheet.subsurface(pygame.Rect(x, 0, state_w, 24)).copy()
            else:
                sub = create_placeholder(state_w, 24, "button")
            slices.append(make_nine_slice(sub, corner=corner))

        self._button_slices = slices
        return slices

    def get_building_sprite(
        self,
        building_id: str,
        width_tiles: int,
        height_tiles: int,
        is_active: bool,
        anim_tick: int = 0,
    ) -> pygame.Surface | None:
        """Load building sprite strip from img/buildings/<id>.png or return None if missing.

        Frame size = footprint * 16 (width_tiles * 16, height_tiles * 16).
        Frame 0 = offline; Frames 1..N = running animation.
        """
        img_file = IMG_DIR / "buildings" / f"{building_id}.png"
        if not img_file.exists():
            return None

        key = f"bld_{building_id}"
        if key not in self.images:
            try:
                raw_surf = pygame.image.load(str(img_file))
                if pygame.display.get_surface() is not None:
                    raw_surf = raw_surf.convert_alpha()
                self.images[key] = raw_surf
            except Exception as exc:
                logger.warning("Failed loading building image %s: %s", img_file, exc)
                return None

        strip = self.images[key]
        fw = width_tiles * 16
        fh = height_tiles * 16
        frames = load_sprite_strip(strip, fw, fh)
        if not frames:
            return None

        if not is_active:
            return frames[0]

        if len(frames) > 1:
            frame_idx = 1 + (anim_tick // 4) % (len(frames) - 1)
            return frames[frame_idx]
        return frames[0]

    def get_fx(self, name: str, frame_w: int, frame_h: int, frame_idx: int) -> pygame.Surface | None:
        """Load FX animation frame from img/fx/<name>.png or return None if missing."""
        fx_file = IMG_DIR / "fx" / f"{name}.png"
        if not fx_file.exists():
            return None

        key = f"fx_{name}"
        if key not in self.images:
            try:
                raw_surf = pygame.image.load(str(fx_file))
                if pygame.display.get_surface() is not None:
                    raw_surf = raw_surf.convert_alpha()
                self.images[key] = raw_surf
            except Exception as exc:
                logger.warning("Failed loading fx %s: %s", fx_file, exc)
                return None

        frames = load_sprite_strip(self.images[key], frame_w, frame_h)
        if not frames:
            return None
        return frames[frame_idx % len(frames)]

    def get_event_image(self, event_id: str) -> pygame.Surface | None:
        """Load event alert illustration from img/events/<event_id>.png or return None."""
        ev_file = IMG_DIR / "events" / f"{event_id}.png"
        if not ev_file.exists():
            return None

        key = f"ev_{event_id}"
        if key not in self.images:
            try:
                raw_surf = pygame.image.load(str(ev_file))
                if pygame.display.get_surface() is not None:
                    raw_surf = raw_surf.convert_alpha()
                self.images[key] = raw_surf
            except Exception as exc:
                logger.warning("Failed loading event image %s: %s", ev_file, exc)
                return None
        return self.images[key]

    def get_next_arrow(self, blink_tick: int) -> pygame.Surface | None:
        """Load blinking advance prompt from img/ui/next_arrow.png or return None."""
        arrow_file = IMG_DIR / "ui" / "next_arrow.png"
        if not arrow_file.exists():
            return None

        key = "next_arrow_surf"
        if key not in self.images:
            try:
                raw_surf = pygame.image.load(str(arrow_file))
                if pygame.display.get_surface() is not None:
                    raw_surf = raw_surf.convert_alpha()
                self.images[key] = raw_surf
            except Exception:
                return None

        frames = load_sprite_strip(self.images[key], 8, 8)
        if not frames:
            return None
        return frames[(blink_tick // 15) % len(frames)]

    def init_cursor(self) -> None:
        """Initialize custom mouse cursor from img/ui/cursor.png if present."""
        cursor_file = IMG_DIR / "ui" / "cursor.png"
        if not cursor_file.exists():
            return
        try:
            cur_surf = pygame.image.load(str(cursor_file)).convert_alpha()
            # 32x16 contains 2 frames: (0, 0, 16, 16) normal, (16, 0, 16, 16) pointing
            normal_frame = cur_surf.subsurface(pygame.Rect(0, 0, 16, 16))
            cursor = pygame.cursors.Cursor((0, 0), normal_frame)
            pygame.mouse.set_cursor(cursor)
        except Exception as exc:
            logger.debug("Custom cursor initialization skipped: %s", exc)


# Global singleton instance
assets = AssetManager()
