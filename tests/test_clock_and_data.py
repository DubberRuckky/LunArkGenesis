# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for pure-Python TickClock and data loading layer.

Ensures zero pygame dependencies in game/logic/ and verifies fixed-rate ticks,
pause/speed switching, warp drop, and robust JSON fallback handling.
"""

from game.logic.clock import TickClock
from game.logic.data import (
    DEFAULT_BALANCE,
    DEFAULT_TEXT,
    DEFAULT_THEME,
    load_balance,
    load_json_file,
    load_text,
    load_theme,
)


def test_clock_initial_state() -> None:
    """Verifies default initialization of TickClock."""
    clock = TickClock(tick_rate=1.0, initial_speed=1)
    assert not clock.is_paused()
    assert clock.get_speed() == 1
    assert clock.get_total_ticks() == 0


def test_clock_ticks_at_1x() -> None:
    """Verifies that 1 second of dt yields exactly 1 tick at 1x speed."""
    clock = TickClock(tick_rate=1.0, initial_speed=1)

    # 0.5s dt gives 0 ticks
    assert clock.update(0.5) == 0
    assert clock.get_total_ticks() == 0

    # Another 0.5s dt completes the second and yields 1 tick
    assert clock.update(0.5) == 1
    assert clock.get_total_ticks() == 1

    # Large dt (3.2s) yields 3 ticks with 0.2s accumulator remaining
    assert clock.update(3.2) == 3
    assert clock.get_total_ticks() == 4


def test_clock_speed_multipliers() -> None:
    """Verifies that 2x, 4x, and 8x speed scale dt correctly."""
    clock = TickClock(tick_rate=1.0, initial_speed=2)
    # At 2x, 0.5s yields 1 tick
    assert clock.update(0.5) == 1

    clock.set_speed(4)
    # At 4x, 0.5s yields 2 ticks
    assert clock.update(0.5) == 2

    clock.set_speed(8)
    # At 8x, 0.5s yields 4 ticks
    assert clock.update(0.5) == 4


def test_clock_pause_and_resume() -> None:
    """Verifies pause stops ticks and resume restores speed."""
    clock = TickClock(tick_rate=1.0, initial_speed=4)

    clock.pause()
    assert clock.is_paused()
    assert clock.get_speed() == 0
    assert clock.update(10.0) == 0

    clock.resume()
    assert not clock.is_paused()
    assert clock.get_speed() == 4
    # Now it ticks again at 4x
    assert clock.update(1.0) == 4

    clock.toggle_pause()
    assert clock.is_paused()
    clock.toggle_pause()
    assert not clock.is_paused()
    assert clock.get_speed() == 4


def test_clock_drop_to_1x() -> None:
    """Verifies drop_to_1x reduces warp speed but leaves 1x or paused alone."""
    clock = TickClock(tick_rate=1.0, initial_speed=4)
    clock.drop_to_1x()
    assert clock.get_speed() == 1

    # Dropping again keeps 1x
    clock.drop_to_1x()
    assert clock.get_speed() == 1

    # While paused, drop_to_1x does not force unpause
    clock.pause()
    clock.drop_to_1x()
    assert clock.is_paused()


def test_data_loader_fallbacks() -> None:
    """Verifies JSON data loaders return valid data even for nonexistent files."""
    fallback_data = {"test_key": 42}
    result = load_json_file("nonexistent_file_xyz.json", fallback_data)
    assert result == fallback_data

    # Real files return non-empty dicts with expected keys
    bal = load_balance()
    assert "cycle" in bal
    assert "indicators" in bal
    assert bal["cycle"]["day_ticks"] == 180

    txt = load_text()
    assert "title" in txt
    assert "game" in txt
    assert "win" in txt
    assert "lose" in txt

    thm = load_theme()
    assert "bars" in thm
    assert "energy" in thm["bars"]
