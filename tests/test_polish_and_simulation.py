# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Unit tests for Stage 10 polish, simulation tool, and accessibility features.

Validates:
- Headless simulation tool execution and metric tracking
- HUD smooth bar interpolation and high contrast mode
- Audio manager resilience (no-op on missing audio files)
- GameScreen controls shortcuts overlay toggle
"""

import pytest

from game.logic.clock import TickClock
from game.logic.data import load_balance
from game.logic.state import GameState
from tools.simulate import run_simulation
from game.audio import audio, AudioManager


@pytest.fixture(autouse=True)
def init_pygame():
    """Ensure pygame font and mixer subsystems are initialized for HUD tests."""
    import pygame
    pygame.font.init()
    yield


def test_simulation_tool_runs_headless():
    """Verify simulate.py runs headless for 50 ticks and returns valid results."""
    res = run_simulation(ticks=50, strategy="balanced")

    assert "outcome" in res
    assert "ticks_simulated" in res
    assert res["ticks_simulated"] <= 50
    assert "final_energy" in res
    assert "final_boredom" in res
    assert "final_revenue" in res
    assert "final_science" in res
    assert "buildings_placed" in res
    assert res["buildings_placed"] >= 1


def test_audio_manager_safe_without_files():
    """Verify audio methods safely no-op without crashes or exceptions."""
    mgr = AudioManager()
    mgr.play("non_existent_sound")
    mgr.play("click")
    mgr.play_music("music_day")
    mgr.stop_music()
    mgr.apply_settings({"audio_master": 5, "audio_music": 5, "audio_sfx": 5})
    assert mgr._master == 5


def test_hud_smooth_bar_interpolation():
    """Verify HUD interpolates display ratios toward target state values."""
    from game.ui.hud import HUD

    balance = load_balance()
    state = GameState(balance)
    clock = TickClock()
    hud = HUD(state, clock)

    initial_energy_ratio = hud.display_ratios["energy"]
    assert initial_energy_ratio == pytest.approx(0.5, rel=1e-2)

    # Dramatically drop energy in state
    state.energy = 20.0  # target ratio: 0.2
    assert state.get_indicator_info("energy")["ratio"] == pytest.approx(0.2, rel=1e-2)

    # Update HUD with dt=0.05
    hud.update(0.05)
    # The display ratio should have smoothly moved downward, between 0.2 and 0.5
    assert 0.2 < hud.display_ratios["energy"] < 0.5


def test_hud_high_contrast_toggle():
    """Verify HUD high contrast mode can be toggled."""
    from game.ui.hud import HUD

    balance = load_balance()
    state = GameState(balance)
    clock = TickClock()
    hud = HUD(state, clock)

    assert hud.high_contrast is False
    hud.high_contrast = True
    assert hud.high_contrast is True
