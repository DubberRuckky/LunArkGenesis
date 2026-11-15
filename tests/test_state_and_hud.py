# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for Stage 2: GameState indicators, thresholds, and HUD logic.

Verifies pure-Python simulation behavior:
- 5 indicators with bounds clamping
- Boredom natural rise and late-game bump
- Event bar fill/drain mechanics based on boredom
- Warning threshold detection and drop_to_1x hook
"""

from game.logic.clock import TickClock
from game.logic.state import GameState


def test_game_state_initial_values() -> None:
    """Verifies starting values loaded from balance.json."""
    state = GameState()
    assert state.energy == 50.0
    assert state.science == 0.0
    assert state.boredom == 10.0
    assert state.revenue == 150.0
    assert state.event == 0.0


def test_boredom_progression_and_late_bump() -> None:
    """Verifies that boredom increases each tick, with an extra bump in later cycles."""
    state = GameState()
    initial_boredom = state.boredom

    # Tick 1 in cycle 1: base change is +0.2
    state.tick(cycle=1)
    assert round(state.boredom - initial_boredom, 2) == 0.2

    # In cycle 2: base change is +0.2 + 0.1 late_bump = +0.3
    prev_boredom = state.boredom
    state.tick(cycle=2)
    assert round(state.boredom - prev_boredom, 2) == 0.3


def test_event_fill_and_drain_logic() -> None:
    """Verifies Event bar fills when boredom is high and drains when low."""
    state = GameState()

    # Low boredom (< 30): Event drains by 0.4 (clamped at 0)
    state.boredom = 20.0
    state.event = 10.0
    state.tick()
    assert round(state.event, 2) == 9.6

    # High boredom (> 60): Event fills by 0.8
    state.boredom = 70.0
    prev_event = state.event
    state.tick()
    assert round(state.event - prev_event, 2) == 0.8


def test_warning_thresholds_and_warp_drop_hook() -> None:
    """Verifies warning triggers when thresholds are crossed and drops clock to 1x."""
    clock = TickClock(tick_rate=1.0, initial_speed=4)
    state = GameState()
    state.on_warning_fired = clock.drop_to_1x

    assert not state.warnings["energy"]
    assert clock.get_speed() == 4

    # Force energy below warning threshold (<= 15)
    state.energy = 10.0
    state.tick()

    assert state.warnings["energy"]
    # Clock speed should have dropped to 1x via hook
    assert clock.get_speed() == 1


def test_indicator_info_and_explanations() -> None:
    """Verifies indicator info dictionary contains kid-friendly sentences and reasons."""
    state = GameState()
    info = state.get_indicator_info("energy")

    assert info["name"] == "Energy"
    assert info["value"] == 50
    assert info["max"] == 100
    assert len(info["desc"]) > 0
    assert len(info["why"]) > 0

    # Test why changes when dropping
    state.deltas["energy"] = -5.0
    info_drop = state.get_indicator_info("energy")
    assert "dropping" in info_drop["why"].lower() or "decreasing" in info_drop["why"].lower()
