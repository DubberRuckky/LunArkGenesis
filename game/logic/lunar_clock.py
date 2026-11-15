# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python lunar day/night cycle and atmospheric clock for LunArk: Genesis.

Strictly NO pygame imports.
Tracks 180s day and 180s night cycles, cycle count (1 of 3), solar ramp-down,
night heating energy drain, dusk warnings, and battery life forecasts.
"""

from typing import Any, Callable

from game.logic.data import load_balance


class LunarClock:
    """Manages lunar diurnal phases, dusk warnings, and night heating load."""

    def __init__(self, balance_data: dict[str, Any] | None = None) -> None:
        self.balance: dict[str, Any] = balance_data or load_balance()
        cycle_cfg = self.balance.get("cycle", {})

        self.day_ticks: int = int(cycle_cfg.get("day_ticks", 180))
        self.night_ticks: int = int(cycle_cfg.get("night_ticks", 180))
        self.total_cycles_to_win: int = int(cycle_cfg.get("total_cycles_to_win", 3))
        self.dusk_warning_ticks: int = int(cycle_cfg.get("dusk_warning_ticks", 30))
        self.night_heating_power_loss: float = float(cycle_cfg.get("night_heating_power_loss", 3.0))

        # Runtime state
        self.cycle: int = 1
        self.is_day: bool = True
        self.phase_ticks: int = 0
        self.total_ticks: int = 0

        self.dusk_warning_active: bool = False
        self.first_night_explained: bool = False
        self.show_night_popup: bool = False

        # Transition hooks
        self.on_dusk: Callable[[], None] | None = None
        self.on_dawn: Callable[[], None] | None = None

    def tick(self) -> dict[str, Any]:
        """Advance lunar cycle by 1 second tick.

        Returns:
            dict[str, Any]: Cycle status summary including phase, warnings, and transitions.
        """
        self.phase_ticks += 1
        self.total_ticks += 1

        dusk_just_started = False
        dawn_just_started = False

        if self.is_day:
            # Check 30s before dusk warning
            if self.phase_ticks >= (self.day_ticks - self.dusk_warning_ticks):
                self.dusk_warning_active = True
            else:
                self.dusk_warning_active = False

            # Transition from Day to Night
            if self.phase_ticks >= self.day_ticks:
                self.is_day = False
                self.phase_ticks = 0
                self.dusk_warning_active = False
                dusk_just_started = True

                # First-time explanation popup
                if not self.first_night_explained:
                    self.show_night_popup = True
                    self.first_night_explained = True

                if self.on_dusk is not None:
                    self.on_dusk()

        else:
            self.dusk_warning_active = False

            # Transition from Night to Dawn
            if self.phase_ticks >= self.night_ticks:
                self.is_day = True
                self.phase_ticks = 0
                self.cycle += 1
                dawn_just_started = True

                if self.on_dawn is not None:
                    self.on_dawn()

        return {
            "cycle": self.cycle,
            "is_day": self.is_day,
            "phase_ticks": self.phase_ticks,
            "phase_duration": self.day_ticks if self.is_day else self.night_ticks,
            "dusk_warning_active": self.dusk_warning_active,
            "dusk_just_started": dusk_just_started,
            "dawn_just_started": dawn_just_started,
            "show_night_popup": self.show_night_popup,
        }

    def get_solar_efficiency(self) -> float:
        """Calculate solar output factor (0.0 to 1.0) with dawn and dusk ramping."""
        if not self.is_day:
            return 0.0

        # Optional smooth ramp at dawn (first 5 ticks) and dusk (last 5 ticks)
        ramp_ticks = 5
        if self.phase_ticks < ramp_ticks:
            return max(0.2, (self.phase_ticks + 1) / (ramp_ticks + 1))
        remaining = self.day_ticks - self.phase_ticks
        if remaining <= ramp_ticks:
            return max(0.2, remaining / (ramp_ticks + 1))

        return 1.0

    def get_heating_load(self) -> float:
        """Return the extra Energy drain per tick during night (0.0 during day)."""
        return 0.0 if self.is_day else self.night_heating_power_loss

    def get_phase_ratio(self) -> float:
        """Return completion ratio of current phase (0.0 to 1.0)."""
        duration = self.day_ticks if self.is_day else self.night_ticks
        return max(0.0, min(1.0, self.phase_ticks / float(duration) if duration > 0 else 0.0))

    def get_night_tint_alpha(self) -> float:
        """Calculate smooth darkness alpha factor (0.0 = bright day, 1.0 = deep night)."""
        transition_duration = 10.0
        if self.is_day:
            remaining = self.day_ticks - self.phase_ticks
            if remaining < transition_duration:
                # Smooth darkening into night
                return max(0.0, min(1.0, (transition_duration - remaining) / transition_duration))
            return 0.0
        else:
            if self.phase_ticks < transition_duration:
                # Smoothly transitioning from day
                return 1.0
            remaining = self.night_ticks - self.phase_ticks
            if remaining < transition_duration:
                # Smooth brightening toward dawn
                return max(0.0, min(1.0, remaining / transition_duration))
            return 1.0

    def get_battery_forecast(self, current_energy: float, net_energy_delta: float) -> int | None:
        """Forecast seconds of remaining battery life before power reaches 0.

        Args:
            current_energy: Current stored Energy.
            net_energy_delta: Total net energy change per tick.

        Returns:
            int | None: Forecasted seconds if draining, None if stable or charging.
        """
        if net_energy_delta < -0.01 and current_energy > 0:
            return int(current_energy / abs(net_energy_delta))
        return None
