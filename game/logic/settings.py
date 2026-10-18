# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Settings model, defaults, validation, and persistence.

This module is pure Python — NO pygame imports allowed.
All display and performance options are loaded, validated, and saved to saves/settings.json.
"""

from copy import deepcopy
import json
import logging
from pathlib import Path
from typing import Any

from game.constants import (
    AVAILABLE_RESOLUTIONS,
    DEFAULT_FPS,
    DEFAULT_RESOLUTION,
    FPS_OPTIONS,
    SAVE_DIR,
    SETTINGS_FILE,
)

logger = logging.getLogger("lunark.settings")

# Default settings according to Phase 1 & Section 3 requirements:
# First launch starts in fullscreen at desktop resolution (handled by display adapter).
# Integer scaling default is On.
DEFAULTS: dict[str, Any] = {
    "fullscreen": True,
    "resolution": list(DEFAULT_RESOLUTION),
    "fps_cap": DEFAULT_FPS,
    "vsync": True,
    "show_fps": False,
    "integer_scaling": True,
}


def get_defaults() -> dict[str, Any]:
    """Return an isolated deep copy of the default settings dict.

    Returns:
        dict[str, Any]: Default setting key-value pairs.
    """
    return deepcopy(DEFAULTS)


def validate_settings(
    settings: dict[str, Any],
    available_resolutions: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """Validate and sanitize a settings dictionary against allowed values.

    Invalid or missing values fall back to defaults, and unsupported keys
    are dropped cleanly.

    Args:
        settings: Raw dictionary of settings.
        available_resolutions: Optional list of supported (w, h) tuples.

    Returns:
        dict[str, Any]: Cleaned and validated settings dictionary.
    """
    defaults = get_defaults()
    cleaned: dict[str, Any] = {}
    allowed_resolutions = available_resolutions or AVAILABLE_RESOLUTIONS

    # 1. Fullscreen
    val = settings.get("fullscreen")
    if isinstance(val, bool):
        cleaned["fullscreen"] = val
    else:
        logger.warning("Invalid fullscreen setting %r, resetting to %r", val, defaults["fullscreen"])
        cleaned["fullscreen"] = defaults["fullscreen"]

    # 2. Resolution: list or tuple of 2 ints, must match allowed resolutions
    res_val = settings.get("resolution")
    valid_res = False
    if isinstance(res_val, (list, tuple)) and len(res_val) == 2:
        try:
            w, h = int(res_val[0]), int(res_val[1])
            if (w, h) in allowed_resolutions:
                cleaned["resolution"] = [w, h]
                valid_res = True
        except (ValueError, TypeError):
            valid_res = False

    if not valid_res:
        logger.warning("Invalid resolution %r, resetting to %r", res_val, defaults["resolution"])
        cleaned["resolution"] = list(defaults["resolution"])

    # 3. FPS Cap
    fps_val = settings.get("fps_cap")
    if isinstance(fps_val, int) and fps_val in FPS_OPTIONS:
        cleaned["fps_cap"] = fps_val
    else:
        logger.warning("Invalid fps_cap %r, resetting to %r", fps_val, defaults["fps_cap"])
        cleaned["fps_cap"] = defaults["fps_cap"]

    # 4. VSync
    vsync_val = settings.get("vsync")
    if isinstance(vsync_val, bool):
        cleaned["vsync"] = vsync_val
    else:
        logger.warning("Invalid vsync %r, resetting to %r", vsync_val, defaults["vsync"])
        cleaned["vsync"] = defaults["vsync"]

    # 5. Show FPS
    show_fps_val = settings.get("show_fps")
    if isinstance(show_fps_val, bool):
        cleaned["show_fps"] = show_fps_val
    else:
        logger.warning("Invalid show_fps %r, resetting to %r", show_fps_val, defaults["show_fps"])
        cleaned["show_fps"] = defaults["show_fps"]

    # 6. Integer Scaling
    int_scale_val = settings.get("integer_scaling")
    if isinstance(int_scale_val, bool):
        cleaned["integer_scaling"] = int_scale_val
    else:
        logger.warning(
            "Invalid integer_scaling %r, resetting to %r",
            int_scale_val,
            defaults["integer_scaling"],
        )
        cleaned["integer_scaling"] = defaults["integer_scaling"]

    return cleaned


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Load settings from JSON file. If missing or corrupt, fall back to defaults.

    Args:
        path: Optional file path. Defaults to constants.SETTINGS_FILE.

    Returns:
        dict[str, Any]: Validated settings dictionary.
    """
    target_path = path or SETTINGS_FILE
    if not target_path.exists():
        logger.info("Settings file not found at %s. Using default settings.", target_path)
        return get_defaults()

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning("Settings JSON content is not an object. Reverting to defaults.")
            return get_defaults()
        return validate_settings(data)
    except Exception as exc:
        logger.warning("Failed to parse settings file %s: %s. Using defaults.", target_path, exc)
        return get_defaults()


def save_settings(settings: dict[str, Any], path: Path | None = None) -> bool:
    """Save settings dictionary to JSON file, creating directory if needed.

    Args:
        settings: Validated settings to save.
        path: Optional file path. Defaults to constants.SETTINGS_FILE.

    Returns:
        bool: True on success, False otherwise.
    """
    target_path = path or SETTINGS_FILE
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned = validate_settings(settings)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)
        return True
    except Exception as exc:
        logger.error("Failed to save settings to %s: %s", target_path, exc)
        return False


def settings_changed(old: dict[str, Any], new: dict[str, Any]) -> bool:
    """Check if display-affecting settings changed between two states.

    Used to decide if the 10-second auto-revert confirmation modal is needed.

    Args:
        old: Original settings dictionary.
        new: Proposed settings dictionary.

    Returns:
        bool: True if mode or scaling changed.
    """
    display_keys = ("fullscreen", "resolution", "integer_scaling")
    for key in display_keys:
        if old.get(key) != new.get(key):
            return True
    return False


def needs_display_change(old: dict[str, Any], new: dict[str, Any]) -> bool:
    """Check if window recreation is necessary (resolution or fullscreen toggle).

    Args:
        old: Original settings dictionary.
        new: Proposed settings dictionary.

    Returns:
        bool: True if window surface recreation is required.
    """
    recreate_keys = ("fullscreen", "resolution", "vsync")
    for key in recreate_keys:
        if old.get(key) != new.get(key):
            return True
    return False
