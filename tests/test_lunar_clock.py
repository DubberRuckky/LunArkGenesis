# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for Stage 5: Lunar day/night clock, heating, and forecasts.

Strictly NO pygame imports.
Verifies 180s day / 180s night progression, dusk warning at 30s before night,
drop_to_1x hook at dusk, solar night cutoff, and battery life forecasting.
"""

from game.logic.clock import TickClock
from game.logic.lunar_clock import LunarClock


def test_initial_lunar_clock_state() -> None:
    """Verifies starting conditions: Day phase of Cycle 1."""
    lc = LunarClock()
    assert lc.cycle == 1
    assert lc.is_day
    assert lc.phase_ticks == 0
    assert not lc.dusk_warning_active


def test_dusk_warning_at_30_ticks_before_night() -> None:
    """Verifies warning triggers at tick 150 of 180 in the day phase."""
    lc = LunarClock()
    # Advance to tick 149
    for _ in range(149):
        lc.tick()
    assert not lc.dusk_warning_active

    # Tick 150: (180 - 30) = 150 -> dusk warning activates
    res = lc.tick()
    assert res["dusk_warning_active"]
    assert lc.dusk_warning_active


def test_dusk_transition_and_warp_drop() -> None:
    """Verifies day transitions to night at tick 180 and triggers drop_to_1x."""
    clock = TickClock(tick_rate=1.0, initial_speed=4)
    lc = LunarClock()
    lc.on_dusk = clock.drop_to_1x

    assert clock.get_speed() == 4

    # Advance through entire 180s day
    for _ in range(180):
        lc.tick()

    assert not lc.is_day
    assert lc.phase_ticks == 0
    # Clock speed dropped to 1x at dusk
    assert clock.get_speed() == 1


def test_night_heating_load_and_solar_cutoff() -> None:
    """Verifies heating load is 3.0 at night (0 by day) and solar efficiency is 0 at night."""
    lc = LunarClock()
    assert lc.is_day
    assert lc.get_heating_load() == 0.0
    assert lc.get_solar_efficiency() > 0.0

    # Advance into night
    for _ in range(180):
        lc.tick()

    assert not lc.is_day
    assert lc.get_heating_load() == 3.0
    assert lc.get_solar_efficiency() == 0.0


def test_full_cycle_advancement() -> None:
    """Verifies 180 day + 180 night ticks completes Cycle 1 and advances to Cycle 2."""
    lc = LunarClock()
    assert lc.cycle == 1

    # 180 day ticks -> Night
    for _ in range(180):
        lc.tick()
    assert not lc.is_day
    assert lc.cycle == 1

    # 180 night ticks -> Dawn of Cycle 2
    for _ in range(180):
        lc.tick()
    assert lc.is_day
    assert lc.cycle == 2


def test_battery_forecast_calculation() -> None:
    """Verifies battery lifetime prediction when power is draining."""
    lc = LunarClock()
    # At 50 energy and draining -2/s -> 25 seconds
    forecast = lc.get_battery_forecast(current_energy=50.0, net_energy_delta=-2.0)
    assert forecast == 25

    # Net positive delta (charging) -> None
    forecast_charging = lc.get_battery_forecast(current_energy=50.0, net_energy_delta=3.0)
    assert forecast_charging is None
