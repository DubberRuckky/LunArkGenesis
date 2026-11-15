# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for Stage 3: World grid, collisions, and building placement.

Strictly NO pygame imports.
Verifies pure Python placement validation, obstacle blocking, overlap detection,
cost deduction, demolish refunds, and Habitat Pod protection.
"""

from game.logic.world import WorldGrid


def test_initial_world_state_and_habitat_pod() -> None:
    """Verifies that Habitat Pod is pre-placed at column 20."""
    world = WorldGrid()
    assert world.world_cols == 48
    assert world.surface_row == 10
    assert len(world.buildings) == 1

    hab = world.get_building_at(20)
    assert hab is not None
    assert hab.building_id == "habitat_pod"
    assert hab.col == 20
    assert hab.width == 4
    assert hab.height == 3


def test_cannot_build_out_of_bounds() -> None:
    """Verifies bounds checks prevent building off map edges."""
    world = WorldGrid()
    # Negative column
    ok, reason = world.can_place(col=-1, width=2, cost=10, current_revenue=100)
    assert not ok
    assert "edge" in reason.lower()

    # Overflow right boundary (48 cols total)
    ok, reason = world.can_place(col=47, width=2, cost=10, current_revenue=100)
    assert not ok
    assert "edge" in reason.lower()


def test_cannot_build_on_blocked_obstacles() -> None:
    """Verifies that blocked tiles (boulders, crater center) reject placement."""
    world = WorldGrid()
    # Col 8 has a boulder
    ok, reason = world.can_place(col=8, width=2, cost=10, current_revenue=100)
    assert not ok
    assert "blocked" in reason.lower() or "crater" in reason.lower()

    # Col 7 with width 2 spans into col 8
    ok, reason = world.can_place(col=7, width=2, cost=10, current_revenue=100)
    assert not ok

    # Col 30 is in crater center
    ok, reason = world.can_place(col=30, width=2, cost=10, current_revenue=100)
    assert not ok


def test_cannot_build_overlapping_existing_building() -> None:
    """Verifies that buildings cannot overlap each other."""
    world = WorldGrid()
    # Habitat Pod occupies cols 20, 21, 22, 23
    ok, reason = world.can_place(col=21, width=2, cost=10, current_revenue=100)
    assert not ok
    assert "occupied" in reason.lower()

    ok, reason = world.can_place(col=19, width=2, cost=10, current_revenue=100)
    assert not ok

    # Free column (e.g. col 10) allows placement
    ok, _ = world.can_place(col=10, width=2, cost=10, current_revenue=100)
    assert ok


def test_cannot_build_without_revenue() -> None:
    """Verifies that insufficient revenue blocks placement."""
    world = WorldGrid()
    ok, reason = world.can_place(col=10, width=2, cost=150, current_revenue=50)
    assert not ok
    assert "revenue" in reason.lower()


def test_place_building_and_revenue_deduction() -> None:
    """Verifies that successful placement deducts cost and adds building to grid."""
    world = WorldGrid()
    initial_revenue = 150.0

    ok, inst, new_rev, msg = world.place_building(
        building_id="fuel_cell",
        col=10,
        width=2,
        height=2,
        cost=40,
        current_revenue=initial_revenue,
    )
    assert ok
    assert inst is not None
    assert inst.building_id == "fuel_cell"
    assert new_rev == 110.0
    assert len(world.buildings) == 2


def test_demolish_tool_and_refund() -> None:
    """Verifies demolish refunds a percentage of cost and removes structure."""
    world = WorldGrid()
    # Place a building first
    ok, inst, rev, _ = world.place_building("fuel_cell", 10, 2, 2, 40, 100.0)
    assert ok

    # Demolish it with 50% refund
    ok, demo_inst, new_rev, msg = world.demolish_building(col=10, refund_percent=0.5, current_revenue=rev)
    assert ok
    assert demo_inst == inst
    # 60 + 20 refund = 80
    assert new_rev == 80.0
    assert world.get_building_at(10) is None


def test_habitat_pod_cannot_be_demolished() -> None:
    """Verifies that Habitat Pod is protected from demolition."""
    world = WorldGrid()
    ok, inst, rev, msg = world.demolish_building(col=20, refund_percent=0.5, current_revenue=100.0)
    assert not ok
    assert "required" in msg.lower()
    assert world.get_building_at(20) is not None
