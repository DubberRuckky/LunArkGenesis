# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python win/lose objectives and game condition evaluator for LunArk: Genesis.

Strictly NO pygame imports.
Evaluates:
- Planet Stats research progression (powered ticks)
- Victory condition: Research complete AND 3 full cycles survived
- Defeat conditions: 15 ticks at Energy 0 OR 20 ticks at Boredom 100
- Start grace period immunity
- Reason and single hint selection for Win/Lose debriefing screens
"""

import random
from typing import Any, Callable

from game.logic.data import load_balance, load_text
from game.logic.lunar_clock import LunarClock
from game.logic.state import GameState
from game.logic.world import BuildingInstance


class ObjectiveManager:
    """Manages Planet Stats research goal, victory conditions, and defeat counters."""

    def __init__(
        self,
        balance_data: dict[str, Any] | None = None,
        text_data: dict[str, Any] | None = None,
        seed: int | None = None,
    ) -> None:
        self.balance: dict[str, Any] = balance_data or load_balance()
        self.text_data: dict[str, Any] = text_data or load_text()
        self.rng = random.Random(seed)

        ind_cfg = self.balance.get("indicators", {})
        self.target_research: float = float(ind_cfg.get("science", {}).get("target_to_win", 100.0))
        self.total_cycles_to_win: int = int(self.balance.get("cycle", {}).get("total_cycles_to_win", 3))

        lose_cfg = self.balance.get("lose_conditions", {})
        self.energy_zero_limit: int = int(lose_cfg.get("energy_zero_ticks_limit", 15))
        self.boredom_max_limit: int = int(lose_cfg.get("boredom_max_ticks_limit", 20))

        grace_cfg = self.balance.get("grace_and_recovery", {})
        self.start_grace_ticks: int = int(grace_cfg.get("start_grace_period_ticks", 60))

        # Runtime state
        self.planet_stats_research: float = 0.0
        self.is_research_complete: bool = False

        self.energy_zero_counter: int = 0
        self.boredom_max_counter: int = 0
        self.total_ticks: int = 0

        self.is_won: bool = False
        self.is_lost: bool = False
        self.lose_cause: str | None = None  # "energy" or "boredom"

        # Critical countdown alert
        self.critical_alert: str | None = None

        # Warning hook to drop warp to 1x
        self.on_critical_warning: Callable[[], None] | None = None
        self._critical_fired: bool = False

    def tick(
        self,
        buildings: list[BuildingInstance],
        state: GameState,
        lunar_clock: LunarClock,
    ) -> dict[str, Any]:
        """Evaluate objectives, update research, and check win/lose states."""
        self.total_ticks += 1

        # 1. Planet Stats Research
        # Check if Planet Stats is built, active, and base has power
        has_planet_stats = any(
            b.building_id == "planet_stats" and b.is_active and not b.is_broken
            for b in buildings
        )
        if has_planet_stats and state.energy > 0:
            self.planet_stats_research = min(
                self.target_research,
                self.planet_stats_research + 1.0,
            )
            if self.planet_stats_research >= self.target_research:
                self.is_research_complete = True

        # 2. Victory Check
        # Complete research AND survived three full cycles
        three_cycles_survived = (lunar_clock.cycle > self.total_cycles_to_win) or (
            lunar_clock.cycle == self.total_cycles_to_win and not lunar_clock.is_day and lunar_clock.phase_ticks >= lunar_clock.night_ticks - 1
        )

        if self.is_research_complete and three_cycles_survived:
            self.is_won = True

        # 3. Defeat Check (Immune during start grace period)
        in_grace = self.total_ticks <= self.start_grace_ticks
        self.critical_alert = None

        if not in_grace:
            # Energy zero counter
            if state.energy <= 0.0:
                self.energy_zero_counter += 1
                remaining_s = max(0, self.energy_zero_limit - self.energy_zero_counter)
                self.critical_alert = f"Power is 0! Base shuts down in {remaining_s}s!"

                if not self._critical_fired and self.on_critical_warning is not None:
                    self.on_critical_warning()
                    self._critical_fired = True

                if self.energy_zero_counter >= self.energy_zero_limit:
                    self.is_lost = True
                    self.lose_cause = "energy"
            else:
                self.energy_zero_counter = 0

            # Boredom 100 counter
            if state.boredom >= state.boredom_max:
                self.boredom_max_counter += 1
                remaining_s = max(0, self.boredom_max_limit - self.boredom_max_counter)
                self.critical_alert = f"Crew is upset! Base gives up in {remaining_s}s!"

                if not self._critical_fired and self.on_critical_warning is not None:
                    self.on_critical_warning()
                    self._critical_fired = True

                if self.boredom_max_counter >= self.boredom_max_limit:
                    self.is_lost = True
                    self.lose_cause = "boredom"
            else:
                self.boredom_max_counter = 0

            if self.energy_zero_counter == 0 and self.boredom_max_counter == 0:
                self._critical_fired = False

        return {
            "research_progress": self.get_research_percent(),
            "is_research_complete": self.is_research_complete,
            "is_won": self.is_won,
            "is_lost": self.is_lost,
            "lose_cause": self.lose_cause,
            "critical_alert": self.critical_alert,
        }

    def get_research_percent(self) -> int:
        """Return Planet Stats research percentage (0 to 100)."""
        if self.target_research <= 0:
            return 100
        return int((self.planet_stats_research / self.target_research) * 100)

    def get_goal_banner_text(self, cycle: int) -> str:
        """Return the goal banner string under the HUD."""
        pct = self.get_research_percent()
        template = self.text_data.get("game", {}).get(
            "goal_banner",
            "Goal: Planet Stats {progress}% | Cycle {cycle} of {total_cycles}",
        )
        return template.format(
            progress=pct,
            cycle=min(cycle, self.total_cycles_to_win),
            total_cycles=self.total_cycles_to_win,
        )

    def get_win_hint(self) -> str:
        """Choose exactly one hint from the victory hint list in text.json."""
        hints = self.text_data.get("win", {}).get("hints", [])
        if hints:
            return self.rng.choice(hints)
        return "Excellent base management, Commander!"

    def get_lose_hint(self, cause: str) -> str:
        """Choose exactly one hint from the defeat hint list in text.json keyed to cause."""
        lose_dict = self.text_data.get("lose", {})
        if cause == "boredom":
            hints = lose_dict.get("boredom_hints", [])
        else:
            hints = lose_dict.get("energy_hints", [])

        if hints:
            return self.rng.choice(hints)
        return "Keep a close watch on indicators and battery reserves."
