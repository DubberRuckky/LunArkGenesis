# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python building economy simulation for LunArk: Genesis.

Strictly NO pygame imports.
Evaluates production and consumption across all placed buildings,
handles building on/off states, broken states, solar daylight dependencies,
and unlocks for Tier 2 and Tier 3 structures.
"""

from typing import Any

from game.logic.data import load_buildings
from game.logic.world import BuildingInstance


def is_building_unlocked(
    building_id: str,
    current_science: float,
    current_revenue: float,
    catalogue: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Check whether a building's science and revenue prerequisites are met.

    Args:
        building_id: Identifier of the building (e.g. 'solar_array').
        current_science: Player's current Science score.
        current_revenue: Player's current Revenue balance.
        catalogue: Optional loaded buildings dictionary.

    Returns:
        tuple[bool, str]: (Is unlocked, plain text requirement message).
    """
    cat = catalogue or load_buildings()
    b_def = cat.get(building_id, {})
    req = b_def.get("unlock_req", {"science": 0, "revenue": 0})
    req_sci = req.get("science", 0)
    req_rev = req.get("revenue", 0)

    if current_science < req_sci or current_revenue < req_rev:
        return (
            False,
            f"Locked! Needs {req_sci} Science and ${req_rev} Revenue.",
        )

    return True, "Unlocked and ready to build."


def calculate_building_deltas(
    buildings: list[BuildingInstance],
    catalogue: dict[str, Any] | None = None,
    is_day: bool = True,
    solar_efficiency: float = 1.0,
    heating_load: float = 0.0,
) -> dict[str, float]:
    """Calculate the cumulative resource deltas produced and consumed by all active buildings.

    An unpowered or broken building produces and consumes nothing.
    Solar Arrays produce energy scaled by daylight efficiency and zero at night.
    Night heating load is subtracted from total energy.

    Args:
        buildings: List of placed BuildingInstance objects.
        catalogue: Optional buildings dictionary.
        is_day: True if daytime, False if lunar night.
        solar_efficiency: Output multiplier for solar panels (0.0 to 1.0).
        heating_load: Extra energy drain per tick during night.

    Returns:
        dict[str, float]: Net per-tick changes for energy, revenue, science, boredom.
    """
    cat = catalogue or load_buildings()
    total_energy = 0.0
    total_revenue = 0.0
    total_science = 0.0
    total_boredom = 0.0

    for b in buildings:
        # Off or broken buildings produce and use nothing
        if not b.is_active or b.is_broken:
            continue

        b_def = cat.get(b.building_id, {})
        e_rate = float(b_def.get("energy_rate", 0.0))
        r_rate = float(b_def.get("revenue_rate", 0.0))
        s_rate = float(b_def.get("science_rate", 0.0))
        b_rate = float(b_def.get("boredom_rate", 0.0))

        # Solar array night cutoff, ramp efficiency, and dust factor
        if b.building_id == "solar_array":
            if not is_day:
                e_rate = 0.0
            else:
                e_rate *= solar_efficiency
                if b.dust_level == 1:
                    e_rate *= 0.5
                elif b.dust_level >= 2:
                    e_rate *= 0.2

        total_energy += e_rate
        total_revenue += r_rate
        total_science += s_rate
        total_boredom += b_rate

    # Subtract night heating load
    total_energy -= heating_load

    return {
        "energy": total_energy,
        "revenue": total_revenue,
        "science": total_science,
        "boredom": total_boredom,
    }
