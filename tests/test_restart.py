# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for restart command generation and restart-needed settings logic.

All tests here verify pure Python logic without initializing Pygame.
"""

from pathlib import Path
import sys

from game.constants import DEFAULT_RESOLUTION
from game.logic.restart import build_restart_command
from game.logic.settings import (
    LIVE_KEYS,
    RESTART_KEYS,
    get_defaults,
    load_settings,
    needs_restart,
    save_settings,
)


def test_restart_command_structure() -> None:
    """Verifies that restart command produces a well-formed list with flag last and no duplicates."""
    dummy_exec = "C:\\Python\\python.exe"
    dummy_script = "C:\\Games\\LunArk Genesis\\main.py"
    argv = [dummy_script, "--debug", "--skip-startup", "arg with spaces"]

    cmd = build_restart_command(executable=dummy_exec, argv=argv)

    # 1. Executable is first item
    assert cmd[0] == dummy_exec

    # 2. Absolute script path is second item
    assert cmd[1] == str(Path(dummy_script).resolve())

    # 3. Path/args with spaces remain single items (never joined or split)
    assert "arg with spaces" in cmd
    assert cmd.count("arg with spaces") == 1

    # 4. Flag is last item and never duplicated
    assert cmd[-1] == "--skip-startup"
    assert cmd.count("--skip-startup") == 1

    # 5. Empty argv falls back to main.py
    cmd_empty = build_restart_command(executable=dummy_exec, argv=[])
    assert cmd_empty[0] == dummy_exec
    assert cmd_empty[1] == str(Path("main.py").resolve())
    assert cmd_empty[-1] == "--skip-startup"


def test_needs_restart_and_key_groups() -> None:
    """Verifies key group separation, restart-needed detection, and list/tuple equality."""
    # 1. The two key groups must never overlap
    assert set(RESTART_KEYS).isdisjoint(set(LIVE_KEYS))

    base = get_defaults()

    # 2. True for fullscreen, resolution, integer_scaling, and vsync changes
    fs_change = dict(base, fullscreen=not base["fullscreen"])
    assert needs_restart(base, fs_change)

    res_change = dict(base, resolution=[1920, 1080])
    assert needs_restart(base, res_change)

    scale_change = dict(base, integer_scaling=not base["integer_scaling"])
    assert needs_restart(base, scale_change)

    vsync_change = dict(base, vsync=not base["vsync"])
    assert needs_restart(base, vsync_change)

    # 3. False for live keys (fps_cap, show_fps)
    fps_change = dict(base, fps_cap=144)
    assert not needs_restart(base, fps_change)

    show_fps_change = dict(base, show_fps=not base["show_fps"])
    assert not needs_restart(base, show_fps_change)

    # 4. List vs tuple resolution counts as equal
    running_with_list = dict(base, resolution=[1280, 720])
    saved_with_tuple = dict(base, resolution=(1280, 720))
    assert not needs_restart(running_with_list, saved_with_tuple)


def test_native_resolution_extra_resolutions(tmp_path: Path) -> None:
    """Verifies that custom desktop resolution survives save/load with extra_resolutions."""
    custom_native = (2560, 1600)  # A 16:10 resolution not in standard 16:9 list
    test_file = tmp_path / "settings.json"

    payload = {
        "fullscreen": False,
        "resolution": list(custom_native),
        "fps_cap": 60,
        "vsync": True,
        "show_fps": False,
        "integer_scaling": True,
    }

    # Save with extra resolution passed
    saved = save_settings(payload, path=test_file, extra_resolutions=custom_native)
    assert saved is True

    # Loading with extra resolution accepts it
    loaded_with_extra = load_settings(path=test_file, extra_resolutions=custom_native)
    assert loaded_with_extra["resolution"] == list(custom_native)

    # Loading without extra resolution rejects it and resets to default resolution
    loaded_without_extra = load_settings(path=test_file)
    assert loaded_without_extra["resolution"] == list(DEFAULT_RESOLUTION)
