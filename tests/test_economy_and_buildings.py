# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for Stage 4: Building catalogue, unlock prerequisites, and economy calculation.

Strictly NO pygame imports.
Verifies all 13 building definitions, footprints, production/consumption rates,
on/off switches, broken-state hooks, and tier unlock criteria.
"""

from game.logic.data import load_buildings
from game.logic.economy import calculate_building_deltas, is_building_unlocked
from game.logic.world import BuildingInstance


def test_all_13_buildings_defined_with_correct_footprints() -> None:
    """Verifies all 13 building IDs exist in buildings.json with correct footprints."""
    catalogue = load_buildings()
    expected_footprints = {
        "habitat_pod": [4, 3],
        "fuel_cell": [2, 2],
        "solar_array": [3, 1],
        "nuclear_plant": [3, 3],
        "datacentre": [2, 2],
        "metal_mining": [3, 2],
        "helium3_extraction": [3, 3],
        "gym": [2, 2],
        "cafe": [2, 2],
        "restaurant": [3, 2],
        "lab": [2, 2],
        "land_research": [3, 2],
        "planet_stats": [3, 3],
    }
    assert len(expected_footprints) == 13
    for b_id, fp in expected_footprints.items():
        assert b_id in catalogue, f"Missing building id: {b_id}"
        assert catalogue[b_id]["footprint"] == fp, f"Mismatched footprint for {b_id}"


def test_unlock_requirements() -> None:
    """Verifies that Tier 1 buildings are unlocked immediately and higher tiers require Science and Revenue."""
    cat = load_buildings()

    # Tier 1 Fuel Cell (0 sci, 0 rev)
    unlocked, _ = is_building_unlocked("fuel_cell", current_science=0, current_revenue=0, catalogue=cat)
    assert unlocked

    # Tier 2 Solar Array requires 20 Science and 60 Revenue
    unlocked, msg = is_building_unlocked("solar_array", current_science=10, current_revenue=100, catalogue=cat)
    assert not unlocked
    assert "20 Science" in msg

    unlocked, msg = is_building_unlocked("solar_array", current_science=30, current_revenue=40, catalogue=cat)
    assert not unlocked
    assert "$60 Revenue" in msg

    unlocked, _ = is_building_unlocked("solar_array", current_science=20, current_revenue=60, catalogue=cat)
    assert unlocked


def test_building_production_and_consumption_deltas() -> None:
    """Verifies net resource calculations across active buildings."""
    cat = load_buildings()

    b_hab = BuildingInstance("habitat_pod", col=20, width=4, height=3, cost=0)
    b_fuel = BuildingInstance("fuel_cell", col=10, width=2, height=2, cost=40)
    b_data = BuildingInstance("datacentre", col=12, width=2, height=2, cost=50)
    b_gym = BuildingInstance("gym", col=14, width=2, height=2, cost=35)
    b_lab = BuildingInstance("lab", col=16, width=2, height=2, cost=45)

    deltas = calculate_building_deltas([b_hab, b_fuel, b_data, b_gym, b_lab], catalogue=cat, is_day=True)

    # Net Energy: hab (-1) + fuel (+5) + data (-2) + gym (-1) + lab (-2) = -1.0
    assert deltas["energy"] == -1.0
    # Net Revenue: data (+4) = 4.0
    assert deltas["revenue"] == 4.0
    # Net Science: lab (+1.0) = 1.0
    assert deltas["science"] == 1.0
    # Net Boredom: gym (-0.3) = -0.3
    assert round(deltas["boredom"], 2) == -0.3


def test_turned_off_building_produces_and_uses_nothing() -> None:
    """Verifies that switching a building off drops its production and consumption to zero."""
    cat = load_buildings()

    b_fuel = BuildingInstance("fuel_cell", col=10, width=2, height=2, cost=40)
    # Turn it off
    b_fuel.is_active = False

    deltas = calculate_building_deltas([b_fuel], catalogue=cat, is_day=True)
    assert deltas["energy"] == 0.0


def test_broken_building_produces_and_uses_nothing() -> None:
    """Verifies that a damaged/broken building produces and consumes nothing."""
    cat = load_buildings()

    b_data = BuildingInstance("datacentre", col=10, width=2, height=2, cost=50)
    b_data.is_broken = True

    deltas = calculate_building_deltas([b_data], catalogue=cat, is_day=True)
    assert deltas["energy"] == 0.0
    assert deltas["revenue"] == 0.0


def test_solar_array_day_vs_night() -> None:
    """Verifies that Solar Array produces 10 Energy by day and 0 at night."""
    cat = load_buildings()

    b_solar = BuildingInstance("solar_array", col=10, width=3, height=1, cost=75)

    deltas_day = calculate_building_deltas([b_solar], catalogue=cat, is_day=True)
    assert deltas_day["energy"] == 10.0

    deltas_night = calculate_building_deltas([b_solar], catalogue=cat, is_day=False)
    assert deltas_night["energy"] == 0.0
