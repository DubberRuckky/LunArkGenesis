# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python game state and indicator simulation for LunArk: Genesis.

Strictly NO pygame imports.
Manages the five core simulation indicators: Energy, Science, Boredom, Revenue,
and Event risk, evaluating production, consumption, warning thresholds, and event escalation.
"""

from copy import deepcopy
from typing import Any, Callable

from game.logic.data import load_balance, load_text


class GameState:
    """Encapsulates the five core resource and mood indicators."""

    def __init__(self, balance: dict[str, Any] | None = None) -> None:
        self.balance: dict[str, Any] = balance or load_balance()
        self.text_data: dict[str, Any] = load_text()

        cfg = self.balance.get("indicators", {})

        # Indicator values
        self.energy: float = float(cfg.get("energy", {}).get("start", 50))
        self.science: float = float(cfg.get("science", {}).get("start", 0))
        self.boredom: float = float(cfg.get("boredom", {}).get("start", 10))
        self.revenue: float = float(cfg.get("revenue", {}).get("start", 150))
        self.event: float = float(cfg.get("event", {}).get("start", 0))

        # Max limits
        self.energy_max: float = float(cfg.get("energy", {}).get("max", 100))
        self.science_max: float = float(cfg.get("science", {}).get("max", 1000))
        self.boredom_max: float = float(cfg.get("boredom", {}).get("max", 100))
        self.revenue_max: float = float(cfg.get("revenue", {}).get("max", 1000))
        self.event_max: float = float(cfg.get("event", {}).get("max", 100))

        # Warning thresholds
        self.energy_warn_thresh: float = float(cfg.get("energy", {}).get("warning_threshold", 15))
        self.boredom_warn_thresh: float = float(cfg.get("boredom", {}).get("warning_threshold", 80))
        self.revenue_warn_thresh: float = float(cfg.get("revenue", {}).get("warning_threshold", 20))
        self.event_warn_thresh: float = float(cfg.get("event", {}).get("warning_threshold", 85))

        # Active warning flags
        self.warnings: dict[str, bool] = {
            "energy": False,
            "boredom": False,
            "revenue": False,
            "event": False,
        }

        # Last tick deltas
        self.deltas: dict[str, float] = {
            "energy": 0.0,
            "science": 0.0,
            "boredom": 0.0,
            "revenue": 0.0,
            "event": 0.0,
        }

        # Why-changed custom strings (or None for automatic text.json explanation)
        self.why_messages: dict[str, str | None] = {
            "energy": None,
            "science": None,
            "boredom": None,
            "revenue": None,
            "event": None,
        }

        # Consecutive ticks at critical values (for lose conditions in Stage 7)
        self.energy_zero_ticks: int = 0
        self.boredom_max_ticks: int = 0

        # Event bar full trigger
        self.event_full: bool = False

        # Callback hook triggered when any warning fires for the first time
        self.on_warning_fired: Callable[[], None] | None = None

    def tick(
        self,
        cycle: int = 1,
        external_deltas: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Advance indicator state by one discrete 1-second simulation tick.

        Args:
            cycle: Current day/night cycle number (1, 2, or 3).
            external_deltas: Optional production/consumption deltas from buildings/heating.

        Returns:
            dict[str, Any]: Summary of tick deltas, warnings, and alerts.
        """
        ext = external_deltas or {}
        cfg = self.balance.get("indicators", {})

        # 1. Base changes from balance.json
        d_energy = float(cfg.get("energy", {}).get("base_change", 0.0)) + ext.get("energy", 0.0)
        d_science = float(cfg.get("science", {}).get("base_change", 0.0)) + ext.get("science", 0.0)

        # Boredom rises slowly, with extra bump in later cycles
        boredom_base = float(cfg.get("boredom", {}).get("base_change", 0.2))
        late_cycle = int(cfg.get("boredom", {}).get("late_bump_cycle", 2))
        if cycle >= late_cycle:
            boredom_base += float(cfg.get("boredom", {}).get("late_bump", 0.1))
        d_boredom = boredom_base + ext.get("boredom", 0.0)

        d_revenue = float(cfg.get("revenue", {}).get("base_change", 0.0)) + ext.get("revenue", 0.0)

        # Event bar fills faster when Boredom is high, drains when low
        event_cfg = cfg.get("event", {})
        high_thresh = float(event_cfg.get("boredom_high_threshold", 60.0))
        low_thresh = float(event_cfg.get("boredom_low_threshold", 30.0))
        fill_rate = float(event_cfg.get("fill_rate_boredom_high", 0.8))
        drain_rate = float(event_cfg.get("drain_rate_boredom_low", 0.4))

        if self.boredom >= high_thresh:
            d_event = fill_rate
        elif self.boredom <= low_thresh:
            d_event = -drain_rate
        else:
            d_event = 0.0
        d_event += ext.get("event", 0.0)

        # 2. Store deltas
        self.deltas["energy"] = d_energy
        self.deltas["science"] = d_science
        self.deltas["boredom"] = d_boredom
        self.deltas["revenue"] = d_revenue
        self.deltas["event"] = d_event

        # 3. Apply deltas with bounds clamping
        self.energy = max(0.0, min(self.energy_max, self.energy + d_energy))
        self.science = max(0.0, min(self.science_max, self.science + d_science))
        self.boredom = max(0.0, min(self.boredom_max, self.boredom + d_boredom))
        self.revenue = max(0.0, min(self.revenue_max, self.revenue + d_revenue))
        self.event = max(0.0, min(self.event_max, self.event + d_event))

        # Check full event bar
        self.event_full = self.event >= self.event_max

        # 4. Critical tick counters
        if self.energy <= 0.0:
            self.energy_zero_ticks += 1
        else:
            self.energy_zero_ticks = 0

        if self.boredom >= self.boredom_max:
            self.boredom_max_ticks += 1
        else:
            self.boredom_max_ticks = 0

        # 5. Warning state evaluation
        old_warnings = dict(self.warnings)
        self.warnings["energy"] = self.energy <= self.energy_warn_thresh
        self.warnings["boredom"] = self.boredom >= self.boredom_warn_thresh
        self.warnings["revenue"] = self.revenue <= self.revenue_warn_thresh
        self.warnings["event"] = self.event >= self.event_warn_thresh

        # Check if any new warning fired
        new_warning_fired = any(self.warnings[k] and not old_warnings[k] for k in self.warnings)
        if new_warning_fired and self.on_warning_fired is not None:
            self.on_warning_fired()

        return {
            "deltas": deepcopy(self.deltas),
            "warnings": deepcopy(self.warnings),
            "event_full": self.event_full,
            "new_warning_fired": new_warning_fired,
        }

    def modify_indicator(self, key: str, amount: float) -> None:
        """Modify an indicator value directly with bounds clamping."""
        if key == "energy":
            self.energy = max(0.0, min(self.energy_max, self.energy + amount))
        elif key == "science":
            self.science = max(0.0, min(self.science_max, self.science + amount))
        elif key == "boredom":
            self.boredom = max(0.0, min(self.boredom_max, self.boredom + amount))
        elif key == "revenue":
            self.revenue = max(0.0, min(self.revenue_max, self.revenue + amount))
        elif key == "event":
            self.event = max(0.0, min(self.event_max, self.event + amount))

    def set_indicator(self, key: str, value: float) -> None:
        """Set an indicator value directly with bounds clamping."""
        if key == "energy":
            self.energy = max(0.0, min(self.energy_max, float(value)))
        elif key == "science":
            self.science = max(0.0, min(self.science_max, float(value)))
        elif key == "boredom":
            self.boredom = max(0.0, min(self.boredom_max, float(value)))
        elif key == "revenue":
            self.revenue = max(0.0, min(self.revenue_max, float(value)))
        elif key == "event":
            self.event = max(0.0, min(self.event_max, float(value)))

    def get_indicator_info(self, key: str) -> dict[str, Any]:
        """Return full information for an indicator including hover explanations."""
        val = getattr(self, key, 0.0)
        max_val = getattr(self, f"{key}_max", 100.0)
        delta = self.deltas.get(key, 0.0)
        warn = self.warnings.get(key, False)

        txt_info = self.text_data.get("indicators", {}).get(key, {})
        name = txt_info.get("name", key.capitalize())
        desc = txt_info.get("desc", "")

        # Custom why message or automatic text based on delta
        custom_why = self.why_messages.get(key)
        if custom_why:
            why = custom_why
        elif delta > 0.01:
            why = txt_info.get("why_rising", "Increasing.")
        elif delta < -0.01:
            why = txt_info.get("why_dropping", "Decreasing.")
        else:
            why = "Steady at current rate."

        return {
            "name": name,
            "value": int(val + 0.5),
            "max": int(max_val),
            "ratio": max(0.0, min(1.0, val / max_val if max_val > 0 else 0.0)),
            "delta": delta,
            "warning": warn,
            "desc": desc,
            "why": why,
        }
