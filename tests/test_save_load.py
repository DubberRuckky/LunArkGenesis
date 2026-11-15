# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Unit tests for save and load system (Stage 9).

Validates:
- save_game() serialises state, world, clock, objectives correctly
- load_game() recovers saved state or returns None on corrupt / missing data
- apply_save() restores state onto live simulation objects
- slot_info() returns lightweight metadata
- any_save_exists() returns True/False accurately
- Pure Python — zero pygame imports.
"""

from pathlib import Path
import json
import pytest

from game.logic.save_load import (
    SAVE_VERSION,
    apply_save,
    load_game,
    save_game,
    slot_info,
    any_save_exists,
)
from game.logic.state import GameState
from game.logic.lunar_clock import LunarClock
from game.logic.objectives import ObjectiveManager
from game.logic.world import BuildingInstance, WorldGrid


@pytest.fixture
def mock_save_dir(tmp_path, monkeypatch):
    """Redirect SAVE_DIR to an isolated temporary directory."""
    monkeypatch.setattr("game.logic.save_load.SAVE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def dummy_env():
    """Create minimal simulation objects for save testing."""
    balance = {
        "indicators": {
            "energy": {"initial": 100, "max": 100},
            "science": {"initial": 0, "max": 1000},
            "boredom": {"initial": 10, "max": 100},
            "revenue": {"initial": 100, "max": 5000},
            "event": {"initial": 0, "max": 100},
        },
        "diurnal": {"day_ticks": 180, "night_ticks": 180, "total_cycles": 3},
        "objectives": {
            "planet_stats_cost_per_sec": 6.0,
            "planet_stats_total_science": 100.0,
            "target_cycles": 3,
            "lose_energy_zero_ticks": 15,
            "lose_boredom_max_ticks": 20,
            "start_grace_ticks": 60,
        },
        "world": {"cols": 48, "surface_row": 10},
    }
    state = GameState(balance)
    clock = LunarClock(balance)
    objs = ObjectiveManager(balance, {})
    world = WorldGrid(balance, {"columns": 48, "obstacles": []})

    # Add a sample building
    b = BuildingInstance("fuel_cell", col=10, width=2, height=2, cost=40)
    world.buildings.append(b)

    return state, world, clock, objs


def test_save_and_load_roundtrip(mock_save_dir, dummy_env):
    state, world, clock, objs = dummy_env
    state.energy = 77.0
    state.revenue = 250.0
    clock.cycle = 2
    clock.is_day = False
    objs.planet_stats_research = 42.5

    ok = save_game(
        slot=1,
        player_name="CadetTest",
        play_time=123.4,
        state=state,
        world_grid=world,
        lunar_clock=clock,
        objectives=objs,
    )
    assert ok is True

    # Validate slot_info
    info = slot_info(1)
    assert info is not None
    assert info["player_name"] == "CadetTest"
    assert info["cycle"] == 2
    assert info["play_time"] == 123.4

    # Load and apply to new objects
    data = load_game(1)
    assert data is not None
    assert data["version"] == SAVE_VERSION

    new_state, new_world, new_clock, new_objs = dummy_env
    name = apply_save(data, new_state, new_world, new_clock, new_objs)

    assert name == "CadetTest"
    assert new_state.energy == 77.0
    assert new_state.revenue == 250.0
    assert new_clock.cycle == 2
    assert new_clock.is_day is False
    assert new_objs.planet_stats_research == 42.5
    assert len(new_world.buildings) == 2
    b_ids = [b.building_id for b in new_world.buildings]
    assert "habitat_pod" in b_ids
    assert "fuel_cell" in b_ids


def test_load_missing_slot_returns_none(mock_save_dir):
    assert load_game(1) is None
    assert slot_info(1) is None


def test_load_corrupted_json_returns_none(mock_save_dir):
    corrupt_file = mock_save_dir / "slot2.json"
    corrupt_file.write_text("{this is not valid json!}", encoding="utf-8")

    assert load_game(2) is None
    assert slot_info(2) is None


def test_load_incompatible_version_returns_none(mock_save_dir):
    old_file = mock_save_dir / "slot3.json"
    bad_data = {
        "version": "0.1_old",
        "player_name": "OldPlayer",
        "indicators": {},
        "buildings": [],
        "lunar_clock": {},
        "objectives": {},
    }
    old_file.write_text(json.dumps(bad_data), encoding="utf-8")

    assert load_game(3) is None
    assert slot_info(3) is None


def test_any_save_exists(mock_save_dir, dummy_env):
    state, world, clock, objs = dummy_env
    assert any_save_exists() is False

    save_game(2, "Cadet", 10.0, state, world, clock, objs)
    assert any_save_exists() is True
