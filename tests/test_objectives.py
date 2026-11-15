# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for Stage 7 Objectives, Victory, Defeat and Debriefing logic."""

from game.logic.objectives import ObjectiveManager
from game.logic.state import GameState
from game.logic.lunar_clock import LunarClock
from game.logic.world import BuildingInstance
from game.logic.data import load_balance, load_text


def test_planet_stats_research_progression():
    """Planet stats research advances 1 tick per second when active and energy > 0."""
    mgr = ObjectiveManager()
    state = GameState()
    state.energy = 20.0
    clock = LunarClock()

    planet_bld = BuildingInstance(
        building_id="planet_stats",
        col=5,
        width=3,
        height=2,
        cost=100,
        is_active=True,
    )

    # 1. Active with power -> advances
    res = mgr.tick([planet_bld], state, clock)
    assert mgr.planet_stats_research == 1.0
    assert res["research_progress"] == 1

    # 2. Inactive -> does not advance
    planet_bld.is_active = False
    mgr.tick([planet_bld], state, clock)
    assert mgr.planet_stats_research == 1.0

    # 3. Active but broken -> does not advance
    planet_bld.is_active = True
    planet_bld.is_broken = True
    mgr.tick([planet_bld], state, clock)
    assert mgr.planet_stats_research == 1.0

    # 4. Active but energy is 0 -> does not advance
    planet_bld.is_broken = False
    state.energy = 0.0
    mgr.tick([planet_bld], state, clock)
    assert mgr.planet_stats_research == 1.0


def test_victory_condition():
    """Win requires BOTH planet stats research complete AND 3 full cycles survived."""
    mgr = ObjectiveManager()
    state = GameState()
    state.energy = 50.0
    clock = LunarClock()
    clock.cycle = 1

    planet_bld = BuildingInstance(
        building_id="planet_stats",
        col=5,
        width=3,
        height=2,
        cost=100,
        is_active=True,
    )

    # Set research near completion
    mgr.planet_stats_research = 99.0
    mgr.tick([planet_bld], state, clock)
    assert mgr.is_research_complete is True
    # But only cycle 1 -> not won yet!
    assert mgr.is_won is False

    # Fast forward clock to cycle 4 (survived 3 full cycles)
    clock.cycle = 4
    clock.is_day = True
    mgr.tick([planet_bld], state, clock)
    assert mgr.is_won is True


def test_lose_conditions_and_grace_period():
    """Energy 0 for 15s or Boredom 100 for 20s triggers lose, but only after 60s grace."""
    mgr = ObjectiveManager()
    state = GameState()
    clock = LunarClock()
    buildings = []

    # 1. During 60s grace period, energy 0 does NOT trigger defeat
    state.energy = 0.0
    for _ in range(60):
        mgr.tick(buildings, state, clock)
        assert mgr.is_lost is False
        assert mgr.energy_zero_counter == 0

    assert mgr.total_ticks == 60

    # Now register critical warning hook
    warning_called = []
    mgr.on_critical_warning = lambda: warning_called.append(True)

    # Tick 14 times outside grace period (counters 1 to 14)
    for i in range(1, 15):
        mgr.tick(buildings, state, clock)
        assert mgr.energy_zero_counter == i
        assert mgr.is_lost is False

    assert len(warning_called) == 1  # Triggered critical warning once
    assert mgr.energy_zero_counter == 14

    # 15th tick triggers defeat
    mgr.tick(buildings, state, clock)
    assert mgr.energy_zero_counter == 15
    assert mgr.is_lost is True
    assert mgr.lose_cause == "energy"


def test_boredom_lose_condition():
    """Boredom at 100 for 20 ticks causes lose."""
    mgr = ObjectiveManager()
    state = GameState()
    clock = LunarClock()
    buildings = []

    # Fast-forward past grace
    mgr.total_ticks = 60
    state.energy = 50.0
    state.boredom = 100.0

    for _ in range(19):
        mgr.tick(buildings, state, clock)
        assert mgr.is_lost is False
        assert mgr.boredom_max_counter > 0

    # 20th tick
    mgr.tick(buildings, state, clock)
    assert mgr.is_lost is True
    assert mgr.lose_cause == "boredom"


def test_hint_selection_and_banner():
    """Hint selection returns valid non-empty hint string from text.json."""
    mgr = ObjectiveManager(seed=42)
    win_hint = mgr.get_win_hint()
    assert isinstance(win_hint, str) and len(win_hint) > 0

    energy_hint = mgr.get_lose_hint("energy")
    assert isinstance(energy_hint, str) and len(energy_hint) > 0

    boredom_hint = mgr.get_lose_hint("boredom")
    assert isinstance(boredom_hint, str) and len(boredom_hint) > 0

    banner = mgr.get_goal_banner_text(cycle=2)
    assert "Goal:" in banner
    assert "Cycle 2 of 3" in banner
