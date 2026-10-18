# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for game/logic/settings.py.

All tests here verify pure Python logic without initializing Pygame.
"""

from pathlib import Path
import pytest

from game.constants import DEFAULT_FPS, DEFAULT_RESOLUTION
from game.logic.settings import (
    DEFAULTS,
    get_defaults,
    load_settings,
    needs_display_change,
    save_settings,
    settings_changed,
    validate_settings,
)


def test_get_defaults_returns_independent_copy() -> None:
    """Verifies that get_defaults returns a deepcopy of the default settings."""
    defaults = get_defaults()
    assert defaults == DEFAULTS
    # Modifying returned object must not mutate global DEFAULTS
    defaults["resolution"][0] = 9999
    assert DEFAULTS["resolution"] == list(DEFAULT_RESOLUTION)


def test_validate_valid_settings() -> None:
    """Verifies that valid settings pass through unchanged."""
    sample = {
        "fullscreen": False,
        "resolution": [1920, 1080],
        "fps_cap": 120,
        "vsync": False,
        "show_fps": True,
        "integer_scaling": False,
    }
    validated = validate_settings(sample)
    assert validated == sample


def test_validate_missing_keys_fills_defaults() -> None:
    """Verifies that missing keys receive default values."""
    partial = {"fullscreen": False}
    validated = validate_settings(partial)
    assert validated["fullscreen"] is False
    assert validated["resolution"] == list(DEFAULT_RESOLUTION)
    assert validated["fps_cap"] == DEFAULT_FPS
    assert validated["vsync"] is True
    assert validated["show_fps"] is False
    assert validated["integer_scaling"] is True


def test_validate_extra_keys_dropped() -> None:
    """Verifies that unrecognized keys are cleanly omitted."""
    raw = {
        "fullscreen": True,
        "resolution": [1280, 720],
        "fps_cap": 60,
        "vsync": True,
        "show_fps": False,
        "integer_scaling": True,
        "cheat_mode": True,
        "volume": 100,
    }
    validated = validate_settings(raw)
    assert "cheat_mode" not in validated
    assert "volume" not in validated


def test_validate_bad_types_reset_to_default() -> None:
    """Verifies that invalid data types fall back to defaults without error."""
    bad_data = {
        "fullscreen": "yes",       # should be bool
        "resolution": "1920x1080",  # should be list/tuple
        "fps_cap": "unlimited",     # should be int
        "vsync": 123,               # should be bool
        "show_fps": None,           # should be bool
        "integer_scaling": "true",  # should be bool
    }
    validated = validate_settings(bad_data)
    defaults = get_defaults()
    assert validated == defaults


def test_validate_unsupported_resolution() -> None:
    """Verifies that resolutions outside the allowed list fall back to default."""
    bad_res = {"resolution": [800, 600]}
    validated = validate_settings(bad_res)
    assert validated["resolution"] == list(DEFAULT_RESOLUTION)


def test_validate_resolution_tuple_converted_to_list() -> None:
    """Verifies that tuple resolutions are normalized into JSON-serializable lists."""
    data = {"resolution": (1920, 1080)}
    validated = validate_settings(data)
    assert validated["resolution"] == [1920, 1080]


def test_validate_invalid_fps_cap() -> None:
    """Verifies that invalid frame rate caps fall back to default."""
    bad_fps = {"fps_cap": 75}
    validated = validate_settings(bad_fps)
    assert validated["fps_cap"] == DEFAULT_FPS


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    """Verifies saving settings to disk and reloading them accurately."""
    test_file = tmp_path / "saves" / "settings.json"
    custom = {
        "fullscreen": False,
        "resolution": [1600, 900],
        "fps_cap": 144,
        "vsync": True,
        "show_fps": True,
        "integer_scaling": False,
    }
    saved = save_settings(custom, path=test_file)
    assert saved is True
    assert test_file.exists()

    loaded = load_settings(path=test_file)
    assert loaded == custom


def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    """Verifies that loading a nonexistent file gracefully returns defaults."""
    nonexistent = tmp_path / "does_not_exist.json"
    loaded = load_settings(path=nonexistent)
    assert loaded == get_defaults()


def test_load_corrupt_file_returns_defaults(tmp_path: Path) -> None:
    """Verifies that loading corrupt JSON recovers gracefully to defaults."""
    corrupt_file = tmp_path / "broken.json"
    corrupt_file.write_text("{ this is not valid json : [[", encoding="utf-8")

    loaded = load_settings(path=corrupt_file)
    assert loaded == get_defaults()


def test_settings_changed_detection() -> None:
    """Verifies detection of changes to display mode, resolution, or scaling."""
    old = get_defaults()
    new = get_defaults()

    # No change
    assert not settings_changed(old, new)

    # Resolution changed
    new["resolution"] = [1920, 1080]
    assert settings_changed(old, new)

    # Only show_fps changed (does not need revert confirmation)
    new = get_defaults()
    new["show_fps"] = True
    assert not settings_changed(old, new)


def test_needs_display_change() -> None:
    """Verifies detection of changes that require recreating the pygame window."""
    old = get_defaults()
    new = get_defaults()

    assert not needs_display_change(old, new)

    new["fullscreen"] = not old["fullscreen"]
    assert needs_display_change(old, new)

    new = get_defaults()
    new["integer_scaling"] = not old["integer_scaling"]
    # Integer scaling change needs canvas re-scale, not window recreation
    assert not needs_display_change(old, new)
