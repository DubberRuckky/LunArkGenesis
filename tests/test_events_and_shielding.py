# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for Stage 6: Event system, shielding, dust cleaning, and recovery windows.

Strictly NO pygame imports.
Verifies event trigger from Event bar, countdown timers, warp drop to 1x on warning,
start grace period protection, post-major-event recovery window, regolith shielding,
dust cleaning, and module repairs.
"""

from game.logic.clock import TickClock
from game.logic.events import EventManager
from game.logic.state import GameState
from game.logic.world import BuildingInstance


def test_event_bar_triggers_warning_countdown_and_drop_to_1x() -> None:
    """Verifies that full Event bar starts an active event countdown and triggers drop_to_1x."""
    clock = TickClock(tick_rate=1.0, initial_speed=4)
    state = GameState()
    mgr = EventManager()
    mgr.on_warning = clock.drop_to_1x
    # Advance past start grace period (60s)
    mgr.total_ticks = 100

    assert clock.get_speed() == 4
    assert mgr.active_event is None

    # Event bar full
    state.event = 100.0
    state.event_full = True

    status = mgr.tick(event_bar_full=True, buildings=[], state=state)
    assert mgr.active_event is not None
    assert mgr.countdown > 0
    # Clock dropped to 1x
    assert clock.get_speed() == 1
    # Event bar reset to 0
    assert state.event == 0.0


def test_start_grace_period_prevents_major_disasters() -> None:
    """Verifies that during the first 60 seconds only positive care packages roll."""
    state = GameState()
    mgr = EventManager(seed=42)
    mgr.total_ticks = 10  # Inside start grace period

    state.event_full = True
    mgr.tick(event_bar_full=True, buildings=[], state=state)

    assert mgr.active_event is not None
    assert mgr.active_event["type"] == "positive"
    assert mgr.active_event["id"] == "care_package"


def test_major_event_starts_recovery_window() -> None:
    """Verifies that resolving a major event starts the 45-tick recovery window."""
    state = GameState()
    mgr = EventManager()
    mgr.total_ticks = 100

    # Manually assign major event
    mgr.active_event = {
        "id": "solar_flare",
        "name": "Solar Flare",
        "type": "major",
        "countdown": 1,
        "energy_loss": 30,
        "energy_loss_shielded": 5,
        "boredom_gain": 20,
        "boredom_gain_shielded": 5,
    }
    mgr.countdown = 1

    # Tick 1 resolves event
    status = mgr.tick(event_bar_full=False, buildings=[], state=state)
    assert status["event_resolved"]
    assert mgr.active_event is None
    # Recovery timer set to 45 ticks
    assert mgr.recovery_timer == 45


def test_recovery_window_blocks_subsequent_major_events() -> None:
    """Verifies that no major event can trigger while recovery_timer > 0."""
    state = GameState()
    mgr = EventManager(seed=123)
    mgr.total_ticks = 100
    mgr.recovery_timer = 30  # Active recovery window

    state.event_full = True
    mgr.tick(event_bar_full=True, buildings=[], state=state)

    assert mgr.active_event is not None
    # Must NOT be major
    assert mgr.active_event["type"] != "major"


def test_regolith_shielding_mitigates_solar_flare() -> None:
    """Verifies that shielded Habitat Pod reduces Energy loss from 30 to 5."""
    state = GameState()
    mgr = EventManager()

    hab_unshielded = BuildingInstance("habitat_pod", col=20, width=4, height=3, cost=0)
    assert not hab_unshielded.is_shielded

    # Flare against unshielded base
    state.energy = 50.0
    ev = {
        "id": "solar_flare",
        "type": "major",
        "energy_loss": 30,
        "energy_loss_shielded": 5,
        "boredom_gain": 20,
        "boredom_gain_shielded": 5,
    }
    mgr._resolve_event(ev, [hab_unshielded], state)
    assert state.energy == 20.0  # 50 - 30

    # Shield habitat with regolith
    state.revenue = 100.0
    ok, msg = mgr.shield_building(hab_unshielded, state)
    assert ok
    assert hab_unshielded.is_shielded
    assert state.revenue == 70.0  # 100 - 30

    # Second flare against shielded base
    state.energy = 50.0
    mgr._resolve_event(ev, [hab_unshielded], state)
    assert state.energy == 45.0  # 50 - 5


def test_dust_accumulation_and_cleaning() -> None:
    """Verifies dust storm accumulation on Solar Arrays and cleaning action."""
    state = GameState()
    mgr = EventManager()
    solar = BuildingInstance("solar_array", col=10, width=3, height=1, cost=75)
    assert solar.dust_level == 0

    ev = {"id": "dust", "type": "hazard"}
    mgr._resolve_event(ev, [solar], state)
    assert solar.dust_level == 1

    # Clean solar array
    state.revenue = 50.0
    ok, msg = mgr.clean_solar_array(solar, state, clean_cost=15)
    assert ok
    assert solar.dust_level == 0
    assert state.revenue == 35.0


def test_equipment_failure_and_repair() -> None:
    """Verifies module breakdown and restoration via repair."""
    state = GameState()
    mgr = EventManager(seed=99)
    data = BuildingInstance("datacentre", col=10, width=2, height=2, cost=50)
    assert not data.is_broken

    ev = {"id": "equipment_failure", "type": "hazard"}
    mgr._resolve_event(ev, [data], state)
    assert data.is_broken

    # Repair module
    state.revenue = 50.0
    ok, msg = mgr.repair_building(data, state, repair_cost=25)
    assert ok
    assert not data.is_broken
    assert state.revenue == 25.0
