# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Save and load system for LunArk: Genesis.

Three JSON slots in saves/slot1.json, slot2.json, slot3.json.
Each slot stores: version, player_name, timestamp, play_time,
indicators, buildings, lunar_clock, objectives, cycle.

Pure Python — NO pygame imports.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("lunark.save")

# Schema version — bump if structure changes incompatibly.
SAVE_VERSION = "1.0"
SAVE_DIR = Path(__file__).resolve().parent.parent.parent / "saves"
SLOT_NAMES = ["slot1.json", "slot2.json", "slot3.json"]


def _slot_path(slot: int) -> Path:
    """Return path for a slot index (1, 2, or 3)."""
    idx = max(0, min(2, slot - 1))
    return SAVE_DIR / SLOT_NAMES[idx]


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_game(
    slot: int,
    player_name: str,
    play_time: float,
    state: Any,          # GameState
    world_grid: Any,     # WorldGrid
    lunar_clock: Any,    # LunarClock
    objectives: Any,     # ObjectiveManager
) -> bool:
    """Write game state to a slot file. Returns True on success."""
    import time

    # Serialise buildings list
    buildings_data: list[dict[str, Any]] = []
    for b in world_grid.buildings:
        buildings_data.append({
            "building_id": b.building_id,
            "col": b.col,
            "width": b.width,
            "height": b.height,
            "cost": b.cost,
            "is_active": b.is_active,
            "is_shielded": b.is_shielded,
            "is_broken": b.is_broken,
            "dust_level": b.dust_level,
        })

    save_dict: dict[str, Any] = {
        "version": SAVE_VERSION,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "play_time": round(play_time, 1),
        "player_name": player_name,
        # Five indicators
        "indicators": {
            "energy": state.energy,
            "science": state.science,
            "boredom": state.boredom,
            "revenue": state.revenue,
            "event": state.event,
        },
        # Lunar clock
        "lunar_clock": {
            "cycle": lunar_clock.cycle,
            "is_day": lunar_clock.is_day,
            "phase_ticks": lunar_clock.phase_ticks,
            "total_ticks": lunar_clock.total_ticks,
            "first_night_explained": lunar_clock.first_night_explained,
        },
        # Objectives
        "objectives": {
            "planet_stats_research": objectives.planet_stats_research,
            "is_research_complete": objectives.is_research_complete,
            "total_ticks": objectives.total_ticks,
        },
        # World
        "buildings": buildings_data,
    }

    path = _slot_path(slot)
    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_dict, f, indent=2)
        logger.info("Game saved to slot %d (%s).", slot, path.name)
        return True
    except Exception as exc:
        logger.error("Failed to save slot %d: %s", slot, exc)
        return False


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_game(slot: int) -> dict[str, Any] | None:
    """Read and validate a save slot. Returns None on error or missing file."""
    path = _slot_path(slot)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.error("Could not read save slot %d: %s", slot, exc)
        return None

    if not isinstance(data, dict):
        logger.warning("Save slot %d is not a dict. Ignoring.", slot)
        return None

    if data.get("version") != SAVE_VERSION:
        logger.warning(
            "Save slot %d has version %r, expected %r. Ignoring.",
            slot, data.get("version"), SAVE_VERSION
        )
        return None

    # Quick sanity check for required keys
    required = {"indicators", "buildings", "lunar_clock", "objectives"}
    if not required.issubset(data.keys()):
        logger.warning("Save slot %d is missing required keys. Ignoring.", slot)
        return None

    return data


def apply_save(
    data: dict[str, Any],
    state: Any,
    world_grid: Any,
    lunar_clock: Any,
    objectives: Any,
) -> str:
    """Apply loaded save data to live objects. Returns the player_name."""
    from game.logic.world import BuildingInstance

    # Indicators
    ind = data.get("indicators", {})
    state.energy = float(ind.get("energy", state.energy))
    state.science = float(ind.get("science", state.science))
    state.boredom = float(ind.get("boredom", state.boredom))
    state.revenue = float(ind.get("revenue", state.revenue))
    state.event   = float(ind.get("event",   state.event))

    # Lunar clock
    lc = data.get("lunar_clock", {})
    lunar_clock.cycle = int(lc.get("cycle", 1))
    lunar_clock.is_day = bool(lc.get("is_day", True))
    lunar_clock.phase_ticks = int(lc.get("phase_ticks", 0))
    lunar_clock.total_ticks = int(lc.get("total_ticks", 0))
    lunar_clock.first_night_explained = bool(lc.get("first_night_explained", False))

    # Objectives
    obj = data.get("objectives", {})
    objectives.planet_stats_research = float(obj.get("planet_stats_research", 0.0))
    objectives.is_research_complete = bool(obj.get("is_research_complete", False))
    objectives.total_ticks = int(obj.get("total_ticks", 0))

    # Buildings — clear and re-place
    world_grid.buildings.clear()
    for bd in data.get("buildings", []):
        inst = BuildingInstance(
            building_id=bd["building_id"],
            col=bd["col"],
            width=bd["width"],
            height=bd["height"],
            cost=bd["cost"],
            is_active=bd.get("is_active", True),
        )
        inst.is_shielded = bd.get("is_shielded", False)
        inst.is_broken = bd.get("is_broken", False)
        inst.dust_level = bd.get("dust_level", 0)
        world_grid.buildings.append(inst)

    return str(data.get("player_name", "Commander"))


def slot_info(slot: int) -> dict[str, Any] | None:
    """Return lightweight metadata for a save slot, or None if empty/corrupt."""
    data = load_game(slot)
    if data is None:
        return None
    return {
        "slot": slot,
        "player_name": data.get("player_name", "Commander"),
        "timestamp": data.get("timestamp", ""),
        "play_time": data.get("play_time", 0.0),
        "cycle": data.get("lunar_clock", {}).get("cycle", 1),
    }


def any_save_exists() -> bool:
    """Return True if at least one valid save slot exists."""
    return any(slot_info(s) is not None for s in range(1, 4))
