# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python world grid and building placement logic for LunArk: Genesis.

Strictly NO pygame imports.
Manages the 48-column lunar surface, obstacle collisions, building overlaps,
placement validation, costs, demolish refunds, and initial Habitat Pod placement.
"""

from typing import Any

from game.logic.data import load_balance, load_map


class BuildingInstance:
    """Represents a placed building structure on the lunar surface."""

    def __init__(
        self,
        building_id: str,
        col: int,
        width: int,
        height: int,
        cost: int,
        is_active: bool = True,
    ) -> None:
        self.building_id: str = building_id
        self.col: int = col
        self.width: int = width
        self.height: int = height
        self.cost: int = cost
        self.is_active: bool = is_active
        self.is_shielded: bool = False
        self.is_broken: bool = False
        self.dust_level: int = 0  # 0: clean, 1: light dust, 2: heavy dust

    def occupies(self, col: int) -> bool:
        """Return True if this building occupies the given column index."""
        return self.col <= col < (self.col + self.width)

    def get_columns(self) -> range:
        """Return range of column indices occupied by this building."""
        return range(self.col, self.col + self.width)


class WorldGrid:
    """Simulates the 48-column lunar surface world and placement rules."""

    def __init__(
        self,
        balance_data: dict[str, Any] | None = None,
        map_data: dict[str, Any] | None = None,
        world_cols: int | None = None,
    ) -> None:
        self.balance: dict[str, Any] = balance_data or load_balance()
        self.map_data: dict[str, Any] = map_data or load_map()

        self.world_cols: int = int(world_cols if world_cols is not None else self.map_data.get("world_cols", 48))
        self.surface_row: int = int(self.map_data.get("surface_row", 10))
        self.blocked_tiles: set[int] = set(self.map_data.get("blocked_tiles", [8, 30, 31, 32]))

        self.buildings: list[BuildingInstance] = []

        # Pre-place Habitat Pod (footprint 4x3)
        hab_col = int(self.map_data.get("habitat_col", 20))
        self.habitat = BuildingInstance(
            building_id="habitat_pod",
            col=hab_col,
            width=4,
            height=3,
            cost=0,
            is_active=True,
        )
        self.buildings.append(self.habitat)

    def can_place(
        self,
        col: int,
        width: int,
        cost: int,
        current_revenue: float,
    ) -> tuple[bool, str]:
        """Validate whether a building can be constructed at column `col`.

        Args:
            col: Starting column index (0-based).
            width: Building footprint width in columns.
            cost: Construction cost in Revenue.
            current_revenue: Available player funds.

        Returns:
            tuple[bool, str]: (Success, error message if any).
        """
        # 1. Bounds check
        if col < 0 or (col + width) > self.world_cols:
            return False, "Cannot build beyond map edge."

        # 2. Financial check
        if current_revenue < cost:
            return False, "Not enough Revenue."

        # 3. Obstacle collision (boulders / crater center)
        for c in range(col, col + width):
            if c in self.blocked_tiles:
                return False, "Terrain is blocked by crater or boulder."

        # 4. Overlap with existing buildings
        for b in self.buildings:
            # Check overlap between [col, col + width) and [b.col, b.col + b.width)
            if max(col, b.col) < min(col + width, b.col + b.width):
                return False, "Space is already occupied by a building."

        return True, ""

    def place_building(
        self,
        building_id: str,
        col: int,
        width: int,
        height: int,
        cost: int,
        current_revenue: float,
    ) -> tuple[bool, BuildingInstance | None, float, str]:
        """Place building if valid and deduct cost from revenue."""
        valid, reason = self.can_place(col, width, cost, current_revenue)
        if not valid:
            return False, None, current_revenue, reason

        inst = BuildingInstance(
            building_id=building_id,
            col=col,
            width=width,
            height=height,
            cost=cost,
            is_active=True,
        )
        self.buildings.append(inst)
        new_revenue = current_revenue - cost
        return True, inst, new_revenue, "Building placed successfully."

    def demolish_building(
        self,
        col: int,
        refund_percent: float,
        current_revenue: float,
    ) -> tuple[bool, BuildingInstance | None, float, str]:
        """Demolish building at `col` and grant refund percentage."""
        inst = self.get_building_at(col)
        if not inst:
            if col in self.blocked_tiles:
                self.blocked_tiles.remove(col)
                return True, None, current_revenue, "Obstacle cleared! Space is now open for building."
            return False, None, current_revenue, "No building at this location."

        # Habitat pod cannot be demolished (required for crew!)
        if inst.building_id == "habitat_pod":
            return False, None, current_revenue, "Habitat Pod is required for crew!"

        self.buildings.remove(inst)
        refund = int(inst.cost * refund_percent)
        new_revenue = current_revenue + refund
        return True, inst, new_revenue, f"Demolished. Refunded ${refund}."

    def get_building_at(self, col: int) -> BuildingInstance | None:
        """Find the building occupying the specified column, if any."""
        for b in self.buildings:
            if b.occupies(col):
                return b
        return None

    def get_occupied_columns(self) -> set[int]:
        """Return set of all column indices occupied by buildings."""
        occupied: set[int] = set()
        for b in self.buildings:
            occupied.update(b.get_columns())
        return occupied
