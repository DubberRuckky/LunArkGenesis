# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python hazard and event management system for LunArk: Genesis.

Strictly NO pygame imports.
Manages the six data-driven events: Solar Flare, Micrometeorite, Lunar Dust,
Crew Argument, Equipment Failure, and Earth Care Package.
Handles countdown warnings, regolith shielding, dust cleaning, repairs,
and post-event recovery windows.
"""

from copy import deepcopy
import random
from typing import Any, Callable

from game.logic.data import load_balance, load_events
from game.logic.state import GameState
from game.logic.world import BuildingInstance


class EventManager:
    """Coordinates event triggers from the Event bar, warnings, and hazard resolution."""

    def __init__(
        self,
        events_data: dict[str, Any] | None = None,
        balance_data: dict[str, Any] | None = None,
        seed: int | None = None,
    ) -> None:
        self.events_data: dict[str, Any] = events_data or load_events()
        self.balance: dict[str, Any] = balance_data or load_balance()
        self.rng = random.Random(seed)

        grace_cfg = self.balance.get("grace_and_recovery", {})
        self.start_grace_period_ticks: int = int(grace_cfg.get("start_grace_period_ticks", 60))
        self.major_event_recovery_ticks: int = int(grace_cfg.get("major_event_recovery_ticks", 45))
        self.shield_cost: int = int(self.events_data.get("shielding", {}).get("cost", 30))

        # Runtime state
        self.total_ticks: int = 0
        self.recovery_timer: int = 0
        self.active_event: dict[str, Any] | None = None
        self.countdown: int = 0
        self.last_impact_message: str | None = None

        # Warning hook (e.g. drop warp to 1x)
        self.on_warning: Callable[[], None] | None = None

    def tick(
        self,
        event_bar_full: bool,
        buildings: list[BuildingInstance],
        state: GameState,
    ) -> dict[str, Any]:
        """Advance event timer, process countdowns, and resolve hazards."""
        self.total_ticks += 1
        event_resolved = False

        # Decrement recovery window timer
        if self.recovery_timer > 0:
            self.recovery_timer -= 1

        # 1. Process active event countdown
        if self.active_event is not None:
            self.countdown -= 1
            if self.countdown <= 0:
                self._resolve_event(self.active_event, buildings, state)
                if self.active_event.get("type") == "major":
                    self.recovery_timer = self.major_event_recovery_ticks
                self.active_event = None
                event_resolved = True

        # 2. Check if Event bar is full and trigger new event
        elif event_bar_full:
            # Reset event meter
            state.event = 0.0
            state.event_full = False

            rolled = self._roll_event()
            if rolled:
                self.active_event = deepcopy(rolled)
                self.countdown = int(self.active_event.get("countdown", 5))
                if self.on_warning is not None:
                    self.on_warning()

        return {
            "active_event": deepcopy(self.active_event),
            "countdown": self.countdown,
            "recovery_timer": self.recovery_timer,
            "last_impact": self.last_impact_message,
            "event_resolved": event_resolved,
        }

    def _roll_event(self) -> dict[str, Any] | None:
        """Select an event based on weights, start grace period, and recovery status."""
        event_list = self.events_data.get("events", [])
        if not event_list:
            return None

        # During start grace period: only positive care package allowed
        if self.total_ticks <= self.start_grace_period_ticks:
            for ev in event_list:
                if ev.get("type") == "positive":
                    return ev
            return None

        # During recovery window: major events are blocked to prevent chained failures
        candidates: list[dict[str, Any]] = []
        weights: list[int] = []

        for ev in event_list:
            if self.recovery_timer > 0 and ev.get("type") == "major":
                continue
            candidates.append(ev)
            weights.append(int(ev.get("weight", 10)))

        if not candidates:
            # Fallback to minor/positive
            return next((e for e in event_list if e.get("type") != "major"), None)

        return self.rng.choices(candidates, weights=weights, k=1)[0]

    def _resolve_event(
        self,
        event: dict[str, Any],
        buildings: list[BuildingInstance],
        state: GameState,
    ) -> None:
        """Apply the real gameplay consequences of the triggered event."""
        ev_id = event.get("id")

        if ev_id == "solar_flare":
            # Habitat shielding check
            hab = next((b for b in buildings if b.building_id == "habitat_pod"), None)
            is_shielded = hab.is_shielded if hab else False

            e_loss = float(event.get("energy_loss_shielded" if is_shielded else "energy_loss", 30))
            b_gain = float(event.get("boredom_gain_shielded" if is_shielded else "boredom_gain", 20))

            state.modify_indicator("energy", -e_loss)
            state.modify_indicator("boredom", b_gain)
            self.last_impact_message = (
                f"Solar Flare struck! Base absorbed {int(e_loss)} energy loss."
                if is_shielded
                else f"Solar Flare struck unshielded base! Lost {int(e_loss)} energy."
            )

        elif ev_id == "micrometeorite":
            if buildings:
                target_b = self.rng.choice(buildings)
                if target_b.is_shielded:
                    # 80% absorbed by regolith mound
                    if self.rng.random() < float(event.get("damage_chance_shielded", 0.2)):
                        target_b.is_broken = True
                        self.last_impact_message = f"Meteorite penetrated shield on {target_b.building_id}!"
                    else:
                        self.last_impact_message = f"Meteorite absorbed safely by regolith on {target_b.building_id}!"
                else:
                    target_b.is_broken = True
                    self.last_impact_message = f"Meteorite hit and damaged {target_b.building_id}!"

        elif ev_id == "dust":
            # Deposits dust on solar arrays
            solars = [b for b in buildings if b.building_id == "solar_array"]
            for s in solars:
                s.dust_level = min(2, s.dust_level + 1)
            self.last_impact_message = "Dust storm coated solar arrays! Clean them to restore power."

        elif ev_id == "crew_argument":
            b_gain = float(event.get("boredom_gain", 25))
            state.modify_indicator("boredom", b_gain)
            self.last_impact_message = f"Crew argument over chores raised boredom by +{int(b_gain)}."

        elif ev_id == "equipment_failure":
            # Damage a non-broken building
            candidates = [b for b in buildings if not b.is_broken and b.building_id != "habitat_pod"]
            if not candidates:
                candidates = [b for b in buildings if not b.is_broken]
            if candidates:
                target = self.rng.choice(candidates)
                target.is_broken = True
                self.last_impact_message = f"Equipment failure in {target.building_id}! Repair needed."

        elif ev_id == "care_package":
            b_loss = float(event.get("boredom_loss", 20))
            r_gain = float(event.get("revenue_gain", 40))
            state.modify_indicator("boredom", -b_loss)
            state.modify_indicator("revenue", r_gain)
            self.last_impact_message = f"Earth care package delivered! +${int(r_gain)} and cheer for crew."

    def shield_building(
        self,
        b: BuildingInstance,
        state: GameState,
    ) -> tuple[bool, str]:
        """Cover building with regolith mound for shielding."""
        if b.is_shielded:
            return False, "Building is already shielded."
        if state.revenue < self.shield_cost:
            return False, f"Not enough Revenue (${self.shield_cost} needed)."

        state.modify_indicator("revenue", -self.shield_cost)
        b.is_shielded = True
        return True, "Building covered with protective lunar regolith!"

    def clean_solar_array(
        self,
        b: BuildingInstance,
        state: GameState,
        clean_cost: int = 15,
    ) -> tuple[bool, str]:
        """Clean dust off solar panels."""
        if b.dust_level <= 0:
            return False, "Solar array is already clean."
        if state.revenue < clean_cost:
            return False, f"Not enough Revenue (${clean_cost} needed)."

        state.modify_indicator("revenue", -clean_cost)
        b.dust_level = 0
        return True, "Solar panels cleaned and power restored!"

    def repair_building(
        self,
        b: BuildingInstance,
        state: GameState,
        repair_cost: int = 25,
    ) -> tuple[bool, str]:
        """Repair a damaged building to operational status."""
        if not b.is_broken:
            return False, "Building is not broken."
        if state.revenue < repair_cost:
            return False, f"Not enough Revenue (${repair_cost} needed)."

        state.modify_indicator("revenue", -repair_cost)
        b.is_broken = False
        return True, "Module repaired and operational!"
