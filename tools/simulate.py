#!/usr/bin/env python3
# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Headless simulation tool for balance tuning in LunArk: Genesis.

Runs N ticks (default 1000) headless with a scripted player policy.
Outputs summary statistics on indicators, economy deltas, day/night transitions,
event impacts, and goal progression.

Pure Python — NO pygame imports.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from game.logic.data import (
    load_balance,
    load_buildings,
    load_events,
    load_map,
    load_text,
)
from game.logic.economy import calculate_building_deltas
from game.logic.events import EventManager
from game.logic.lunar_clock import LunarClock
from game.logic.objectives import ObjectiveManager
from game.logic.state import GameState
from game.logic.world import WorldGrid


def run_simulation(ticks: int = 1000, strategy: str = "balanced") -> dict:
    """Run a headless simulation for the given number of ticks."""
    balance = load_balance()
    map_data = load_map()
    buildings_data = load_buildings()
    events_data = load_events()
    text = load_text()

    state = GameState(balance)
    world = WorldGrid(balance, map_data)
    clock = LunarClock(balance)
    events = EventManager(events_data, balance)
    objectives = ObjectiveManager(balance, text)

    # Tracking metrics
    energy_history: list[float] = []
    boredom_history: list[float] = []
    revenue_history: list[float] = []
    science_history: list[float] = []
    events_triggered: list[str] = []

    game_over: str | None = None
    won_at: int | None = None
    lost_at: int | None = None

    # Scripted player build queue (col, building_id)
    # Balanced strategy attempts to expand power, crew comfort, research, and revenue
    build_queue = [
        (24, "fuel_cell"),
        (26, "fuel_cell"),
        (28, "gym"),
        (16, "datacentre"),
        (14, "lab"),
        (30, "solar_array"),
        (10, "metal_mining"),
        (34, "cafe"),
        (36, "land_research"),
        (40, "planet_stats"),
    ]
    next_col = 4

    for tick in range(1, ticks + 1):
        clock.tick()
        is_day = clock.is_day
        solar_eff = clock.get_solar_efficiency()
        heating = clock.get_heating_load()

        # 1. Economy calculation
        b_deltas = calculate_building_deltas(
            world.buildings,
            buildings_data,
            is_day=is_day,
            solar_efficiency=solar_eff,
            heating_load=heating,
        )
        state.tick(cycle=clock.cycle, external_deltas=b_deltas)

        # 2. Events tick
        events.tick(
            event_bar_full=state.event_full,
            buildings=world.buildings,
            state=state,
        )
        if events.active_event and events.active_event["id"] not in events_triggered:
            events_triggered.append(events.active_event["id"])

        # 3. Objectives tick
        obj_status = objectives.tick(
            world.buildings,
            state,
            clock,
        )

        # 4. Scripted player actions
        if strategy == "balanced":
            # Dynamic priorities
            target_build: str | None = None
            if state.energy < 40:
                target_build = "fuel_cell"
            elif state.boredom > 35:
                target_build = "gym"
            elif state.revenue < 80:
                target_build = "datacentre"
            elif state.science < 60:
                target_build = "lab"
            elif objectives.planet_stats_research < 100 and not any(b.building_id == "planet_stats" for b in world.buildings):
                target_build = "planet_stats"
            elif build_queue:
                target_build = build_queue[0][1]

            if target_build:
                b_def = buildings_data.get(target_build)
                if b_def:
                    cost = b_def.get("cost", 0)
                    fp = b_def.get("footprint", [2, 2])
                    width, height = fp[0], fp[1]
                    req = b_def.get("unlock_req", {})
                    req_sci = req.get("science", 0)
                    req_rev = req.get("revenue", 0)

                    can_unlock = state.science >= req_sci and state.revenue >= req_rev
                    can_afford = state.revenue >= cost

                    if can_unlock and can_afford:
                        # Find empty col
                        for col_candidate in range(4, 44):
                            valid, _ = world.can_place(col_candidate, width, cost, state.revenue)
                            if valid:
                                success, inst, new_rev, _ = world.place_building(
                                    building_id=target_build,
                                    col=col_candidate,
                                    width=width,
                                    height=height,
                                    cost=cost,
                                    current_revenue=state.revenue,
                                )
                                if success:
                                    state.revenue = new_rev
                                    if build_queue and build_queue[0][1] == target_build:
                                        build_queue.pop(0)
                                break

        # 5. Record history
        energy_history.append(state.energy)
        boredom_history.append(state.boredom)
        revenue_history.append(state.revenue)
        science_history.append(state.science)

        # Check win/loss
        if obj_status["is_won"] and won_at is None:
            won_at = tick
            game_over = "VICTORY"
        elif obj_status["is_lost"] and lost_at is None:
            lost_at = tick
            game_over = f"DEFEAT ({obj_status.get('lose_cause', 'unknown')})"
            break

    # Compile results summary
    return {
        "ticks_simulated": tick,
        "outcome": game_over or "SURVIVED (In Progress)",
        "won_at": won_at,
        "lost_at": lost_at,
        "cycle_reached": clock.cycle,
        "final_energy": round(state.energy, 1),
        "min_energy": round(min(energy_history), 1) if energy_history else 0,
        "final_boredom": round(state.boredom, 1),
        "max_boredom": round(max(boredom_history), 1) if boredom_history else 0,
        "final_revenue": round(state.revenue, 1),
        "final_science": round(state.science, 1),
        "planet_stats_research": round(objectives.planet_stats_research, 1),
        "buildings_placed": len(world.buildings),
        "events_triggered": events_triggered,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="LunArk Genesis Headless Simulation")
    parser.add_argument("--ticks", type=int, default=1000, help="Number of ticks to simulate (default: 1000)")
    parser.add_argument("--strategy", type=str, default="balanced", choices=["balanced", "passive"], help="Player policy")
    args = parser.parse_args()

    print(f"=== Running LunArk: Genesis Simulation ({args.ticks} ticks, strategy: {args.strategy}) ===")
    res = run_simulation(ticks=args.ticks, strategy=args.strategy)

    print("\n--- Simulation Summary ---")
    print(f"Outcome:              {res['outcome']}")
    print(f"Ticks Elapsed:        {res['ticks_simulated']}")
    print(f"Cycle Reached:        {res['cycle_reached']}/3")
    print(f"Buildings Built:      {res['buildings_placed']}")
    print(f"Events Encountered:   {', '.join(res['events_triggered']) or 'None'}")
    print(f"Energy (Min / Final): {res['min_energy']} / {res['final_energy']}")
    print(f"Boredom (Max / Final):{res['max_boredom']} / {res['final_boredom']}")
    print(f"Revenue (Final):      ${res['final_revenue']}")
    print(f"Science (Final):      {res['final_science']} pts")
    print(f"Planet Stats Progress:{res['planet_stats_research']}%")
    print("====================================================\n")


if __name__ == "__main__":
    main()
