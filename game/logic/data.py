# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Data loaders with friendly fallback handling for LunArk: Genesis.

Pure Python logic — strictly NO pygame imports.
Loads JSON configuration from game/data/ with safe, complete built-in defaults
so gameplay never crashes if a file is missing or damaged.
"""

from copy import deepcopy
import json
import logging
from pathlib import Path
from typing import Any

from game.constants import DATA_DIR

logger = logging.getLogger("lunark.data")

# Fallback definitions
DEFAULT_BALANCE: dict[str, Any] = {
    "tick_rate": 1.0,
    "warp_speeds": [0, 1, 2, 4, 8],
    "cycle": {
        "day_ticks": 180,
        "night_ticks": 180,
        "total_cycles_to_win": 3,
        "dusk_warning_ticks": 30,
        "night_heating_power_loss": 3,
        "_notes": "Day and night length in ticks, cycles needed to win, dusk warning time, and night heating drain.",
    },
    "world": {
        "world_cols": 48,
        "tile_size": 16,
        "surface_row": 10,
        "underground_rows": 4,
        "habitat_start_col": 20,
        "_notes": "48 columns of 16-pixel tiles with ground surface at row 10.",
    },
    "indicators": {
        "energy": {
            "max": 100,
            "start": 50,
            "base_change": 0,
            "warning_threshold": 15,
            "_notes": "Power for the base. Keep it above 0 or lights go out!",
        },
        "science": {
            "max": 1000,
            "start": 0,
            "base_change": 0,
            "warning_threshold": 0,
            "target_to_win": 100,
            "_notes": "Research points to unlock new buildings and complete Planet Stats.",
        },
        "boredom": {
            "max": 100,
            "start": 10,
            "base_change": 0.2,
            "late_bump": 0.1,
            "late_bump_cycle": 2,
            "warning_threshold": 80,
            "_notes": "Crew mood (lower is better). Gyms and cafes keep crew happy.",
        },
        "revenue": {
            "max": 1000,
            "start": 150,
            "base_change": 0,
            "warning_threshold": 20,
            "_notes": "Funds to build, shield, clean, and repair your base.",
        },
        "event": {
            "max": 100,
            "start": 0,
            "fill_rate_boredom_high": 0.8,
            "drain_rate_boredom_low": 0.4,
            "boredom_high_threshold": 60,
            "boredom_low_threshold": 30,
            "warning_threshold": 85,
            "_notes": "Fills faster when crew is bored. A full bar brings an event.",
        },
    },
    "lose_conditions": {
        "energy_zero_ticks_limit": 15,
        "boredom_max_ticks_limit": 20,
        "_notes": "Seconds at zero energy or max boredom before base fails.",
    },
    "grace_and_recovery": {
        "start_grace_period_ticks": 60,
        "major_event_recovery_ticks": 45,
        "_notes": "Peaceful seconds at start and quiet time after major events.",
    },
    "economy": {
        "demolish_refund_percent": 0.5,
        "_notes": "Refund percentage given back when removing a building.",
    },
}

DEFAULT_TEXT: dict[str, Any] = {
    "title": {
        "start_game": "New Game",
        "continue_game": "Continue",
        "settings": "Settings",
        "quit": "Quit",
        "subtitle": "Moon-Base Simulator",
    },
    "pause": {
        "title": "Base Paused",
        "resume": "Resume",
        "settings": "Settings",
        "save": "Save Game",
        "load": "Load Game",
        "quit_to_title": "Quit to Title",
    },
    "game": {
        "goal_banner": "Goal: Planet Stats {progress}% | Cycle {cycle} of {total_cycles}",
        "cycle_day": "Day",
        "cycle_night": "Night",
        "warp_1x": "1x",
        "warp_2x": "2x",
        "warp_4x": "4x",
        "warp_8x": "8x",
        "paused": "PAUSED",
        "dusk_warning": "Solar panels stop at night. Save your power!",
        "battery_forecast": "At this rate, battery lasts about {seconds} seconds.",
        "energy_critical": "Power is empty! Base shuts down in {seconds}s!",
        "boredom_critical": "Crew is upset! Base gives up in {seconds}s!",
    },
    "win": {
        "title": "Mission Accomplished!",
        "reason": "You completed Planet Stats and survived three lunar days!",
        "hints": [
            "Solar arrays make clean energy while the Sun is up.",
            "Fuel cells give steady power when night falls.",
            "A happy crew keeps events from happening too quickly.",
        ],
        "play_again": "Play Again",
        "back_to_title": "Back to Title",
    },
    "lose": {
        "title": "Mission Failed",
        "energy_reason": "The base ran out of power for too long.",
        "boredom_reason": "The crew got too bored and left their posts.",
        "energy_hints": [
            "Build extra fuel cells before the long night begins.",
            "Turn off science buildings at night to save precious power.",
        ],
        "boredom_hints": [
            "Build a Gym or Cafe to cheer up your crew.",
            "Do not let the Event meter fill up all the way.",
        ],
        "play_again": "Try Again",
        "back_to_title": "Back to Title",
    },
    "indicators": {
        "energy": {
            "name": "Energy",
            "desc": "Power available for your lights, heat, and machines.",
            "why_dropping": "Energy is dropping because buildings use power.",
            "why_rising": "Energy is rising from your generators.",
        },
        "science": {
            "name": "Science",
            "desc": "Research points earned by labs to unlock new tech.",
            "why_dropping": "Science points are steady.",
            "why_rising": "Scientists are discovering new lunar data.",
        },
        "boredom": {
            "name": "Boredom",
            "desc": "Crew mood. Lower is better so everyone stays focused.",
            "why_dropping": "The crew is relaxing at fun activities.",
            "why_rising": "Working on the Moon gets lonely over time.",
        },
        "revenue": {
            "name": "Revenue",
            "desc": "Money to spend on new buildings and base repairs.",
            "why_dropping": "Funds spent on construction and maintenance.",
            "why_rising": "Income earned from data and mining operations.",
        },
        "event": {
            "name": "Event",
            "desc": "Risk meter. When full, a major hazard will strike.",
            "why_dropping": "A happy crew helps prevent accidents.",
            "why_rising": "High boredom increases base hazard chances.",
        },
    },
    "science_facts": {
        "regolith": {
            "text": "Regolith is lunar soil made of crushed rock and dust.",
            "verify": True,
        },
        "helium3": {
            "text": "Helium-3 is solar fuel trapped inside Moon soil.",
            "verify": True,
        },
        "lunar_night": {
            "text": "Night on the Moon lasts about 14 Earth days.",
            "verify": True,
        },
    },
}

DEFAULT_THEME: dict[str, Any] = {
    "bars": {
        "energy": [255, 220, 50],
        "science": [80, 180, 255],
        "boredom": [200, 80, 200],
        "revenue": [80, 220, 80],
        "event": [220, 60, 60],
        "bg": [30, 30, 40],
        "border": [80, 80, 100],
    },
    "night_tint": [15, 20, 50, 160],
    "alerts": {
        "warning": [255, 140, 40],
        "danger": [240, 70, 70],
        "success": [80, 220, 80],
        "neutral": [180, 180, 180],
    },
    "placement": {
        "valid": [80, 220, 80],
        "invalid": [220, 60, 60],
    },
    "ui": {
        "padding": 6,
        "panel_bg": [20, 22, 32, 225],
        "panel_border": [90, 95, 115],
        "dialogue_bg": [14, 16, 24, 235],
        "dialogue_border": [100, 110, 140],
        "tooltip_bg": [12, 14, 20, 240],
        "tooltip_border": [120, 125, 150],
        "button_normal": [55, 60, 75],
        "button_hover": [75, 80, 100],
        "button_pressed": [40, 44, 55],
        "button_border": [110, 115, 130],
        "button_text": [230, 230, 230],
    },
}


DEFAULT_MAP: dict[str, Any] = {
    "world_cols": 48,
    "surface_row": 10,
    "habitat_col": 20,
    "blocked_tiles": [8, 30, 31, 32],
    "tile_layout": {},
    "_notes": "Map layout with boulder at col 8, crater at cols 30-32, and habitat starting at col 20.",
}

DEFAULT_BUILDINGS: dict[str, Any] = {
    "habitat_pod": {"category": "habitat", "tier": 1, "footprint": [4, 3], "cost": 0, "energy_rate": -1.0, "revenue_rate": 0.0, "science_rate": 0.0, "boredom_rate": 0.0, "unlock_req": {"science": 0, "revenue": 0}},
    "fuel_cell": {"category": "generator", "tier": 1, "footprint": [2, 2], "cost": 40, "energy_rate": 5.0, "revenue_rate": 0.0, "science_rate": 0.0, "boredom_rate": 0.0, "unlock_req": {"science": 0, "revenue": 0}},
    "solar_array": {"category": "generator", "tier": 2, "footprint": [3, 1], "cost": 75, "energy_rate": 10.0, "revenue_rate": 0.0, "science_rate": 0.0, "boredom_rate": 0.0, "unlock_req": {"science": 20, "revenue": 60}},
    "nuclear_plant": {"category": "generator", "tier": 3, "footprint": [3, 3], "cost": 180, "energy_rate": 25.0, "revenue_rate": 0.0, "science_rate": 0.0, "boredom_rate": 0.0, "unlock_req": {"science": 60, "revenue": 140}},
    "datacentre": {"category": "cashflow", "tier": 1, "footprint": [2, 2], "cost": 50, "energy_rate": -2.0, "revenue_rate": 4.0, "science_rate": 0.0, "boredom_rate": 0.0, "unlock_req": {"science": 0, "revenue": 0}},
    "metal_mining": {"category": "cashflow", "tier": 2, "footprint": [3, 2], "cost": 90, "energy_rate": -4.0, "revenue_rate": 9.0, "science_rate": 0.0, "boredom_rate": 0.0, "unlock_req": {"science": 25, "revenue": 70}},
    "helium3_extraction": {"category": "cashflow", "tier": 3, "footprint": [3, 3], "cost": 160, "energy_rate": -8.0, "revenue_rate": 18.0, "science_rate": 0.0, "boredom_rate": 0.0, "unlock_req": {"science": 55, "revenue": 120}},
    "gym": {"category": "activity", "tier": 1, "footprint": [2, 2], "cost": 35, "energy_rate": -1.0, "revenue_rate": 0.0, "science_rate": 0.0, "boredom_rate": -0.3, "unlock_req": {"science": 0, "revenue": 0}},
    "cafe": {"category": "activity", "tier": 2, "footprint": [2, 2], "cost": 65, "energy_rate": -2.0, "revenue_rate": 0.0, "science_rate": 0.0, "boredom_rate": -0.6, "unlock_req": {"science": 15, "revenue": 50}},
    "restaurant": {"category": "activity", "tier": 3, "footprint": [3, 2], "cost": 120, "energy_rate": -4.0, "revenue_rate": 0.0, "science_rate": 0.0, "boredom_rate": -1.2, "unlock_req": {"science": 45, "revenue": 100}},
    "lab": {"category": "science", "tier": 1, "footprint": [2, 2], "cost": 45, "energy_rate": -2.0, "revenue_rate": 0.0, "science_rate": 1.0, "boredom_rate": 0.0, "unlock_req": {"science": 0, "revenue": 0}},
    "land_research": {"category": "science", "tier": 2, "footprint": [3, 2], "cost": 80, "energy_rate": -4.0, "revenue_rate": 0.0, "science_rate": 2.5, "boredom_rate": 0.0, "unlock_req": {"science": 20, "revenue": 60}},
    "planet_stats": {"category": "science", "tier": 3, "footprint": [3, 3], "cost": 200, "energy_rate": -6.0, "revenue_rate": 0.0, "science_rate": 5.0, "boredom_rate": 0.0, "unlock_req": {"science": 50, "revenue": 150}},
}

DEFAULT_EVENTS: dict[str, Any] = {
    "events": [
        {"id": "solar_flare", "name": "Solar Flare", "type": "major", "weight": 20, "countdown": 10, "energy_loss": 30, "energy_loss_shielded": 5, "boredom_gain": 20, "boredom_gain_shielded": 5, "text": "Solar Flare approaching!"},
        {"id": "micrometeorite", "name": "Micrometeorite", "type": "major", "weight": 20, "countdown": 6, "damage_chance_unshielded": 1.0, "damage_chance_shielded": 0.2, "text": "Micrometeorite detected!"},
        {"id": "dust", "name": "Lunar Dust", "type": "hazard", "weight": 20, "countdown": 5, "clean_cost": 15, "text": "Dust covers solar arrays."},
        {"id": "crew_argument", "name": "Crew Argument", "type": "minor", "weight": 15, "countdown": 4, "boredom_gain": 25, "text": "Crew argument! Morale drops."},
        {"id": "equipment_failure", "name": "Equipment Failure", "type": "hazard", "weight": 15, "countdown": 5, "repair_cost": 25, "repair_ticks": 5, "text": "Equipment failure in a module."},
        {"id": "care_package", "name": "Care Package", "type": "positive", "weight": 10, "countdown": 5, "boredom_loss": 20, "revenue_gain": 40, "text": "Care package arrived from Earth!"},
    ],
    "shielding": {"cost": 30},
}


def load_json_file(filename: str, default_data: dict[str, Any]) -> dict[str, Any]:
    """Load a JSON file from game/data/ with safe fallback and clear logs.

    Args:
        filename: Name of the JSON file (e.g. 'balance.json').
        default_data: Built-in dictionary used if file is missing or invalid.

    Returns:
        dict[str, Any]: Loaded dictionary or a deep copy of default_data.
    """
    path = DATA_DIR / filename
    if not path.exists():
        logger.info("Data file '%s' not found. Using built-in defaults.", filename)
        return deepcopy(default_data)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning("Data file '%s' is not a dictionary. Using defaults.", filename)
            return deepcopy(default_data)
        return data
    except Exception as exc:
        logger.error("Failed to parse data file '%s': %s. Using defaults.", filename, exc)
        return deepcopy(default_data)


def load_balance() -> dict[str, Any]:
    """Load balance numbers from balance.json with fallback."""
    return load_json_file("balance.json", DEFAULT_BALANCE)


def load_text() -> dict[str, Any]:
    """Load text and messages from text.json with fallback."""
    return load_json_file("text.json", DEFAULT_TEXT)


def load_theme() -> dict[str, Any]:
    """Load color theme from theme.json with fallback."""
    return load_json_file("theme.json", DEFAULT_THEME)


def load_map() -> dict[str, Any]:
    """Load world map layout and blocked tiles with fallback."""
    return load_json_file("map.json", DEFAULT_MAP)


def load_buildings() -> dict[str, Any]:
    """Load building definitions, footprints, and costs with fallback."""
    return load_json_file("buildings.json", DEFAULT_BUILDINGS)


def load_events() -> dict[str, Any]:
    """Load hazard event definitions and weights with fallback."""
    return load_json_file("events.json", DEFAULT_EVENTS)


DEFAULT_TUTORIAL: dict[str, Any] = {
    "welcome": {
        "dialogue": [
            "Welcome to the Moon, Commander!",
            "I am Lieutenant Vance. Let us set up your mission.",
        ],
        "name_prompt": "Enter your Commander callsign:",
        "default_name": "Commander",
        "max_name_length": 12,
        "expression": 1,
    },
    "steps": [
        {
            "step_id": 1,
            "title": "Five Base Indicators",
            "target": "hud",
            "expression": 0,
            "dialogue": [
                "These five bars track base health.",
                "Energy powers rooms. Science unlocks tech.",
                "Boredom tracks crew mood. Revenue is your funds.",
                "The Event bar warns of incoming danger.",
            ],
        },
        {
            "step_id": 2,
            "title": "The Habitat Pod",
            "target": "habitat",
            "expression": 1,
            "camera_col": 20,
            "dialogue": [
                "This is our Habitat Pod.",
                "Our astronauts live here.",
                "They need electricity, good food, and fun!",
            ],
        },
        {
            "step_id": 3,
            "title": "Build a Fuel Cell",
            "target": "build_fuel_cell",
            "category": "generator",
            "building_id": "fuel_cell",
            "expression": 2,
            "dialogue": [
                "We need electricity right away.",
                "Open Generator in your Build Tray.",
                "Place a Fuel Cell on the lunar ground!",
            ],
        },
        {
            "step_id": 4,
            "title": "Build a Datacentre",
            "target": "build_datacentre",
            "category": "cashflow",
            "building_id": "datacentre",
            "expression": 0,
            "dialogue": [
                "Expanding our base costs money.",
                "Select Cashflow in the Build Tray.",
                "Place a Datacentre to earn Revenue each second.",
            ],
        },
        {
            "step_id": 5,
            "title": "Lunar Day and Night",
            "target": "day_night_clock",
            "expression": 2,
            "dialogue": [
                "Watch the day and night clock.",
                "The Sun shines for 180 seconds, then darkness falls.",
                "Solar stops at night, and heaters use extra power.",
            ],
        },
        {
            "step_id": 6,
            "title": "The Mission Goal",
            "target": "goal_planet_stats",
            "category": "science",
            "building_id": "planet_stats",
            "expression": 1,
            "dialogue": [
                "Your goal is to build Planet Stats and survive 3 cycles.",
                "Research tech and keep your crew happy.",
                "Good luck, Commander! You are ready to lead.",
            ],
        },
    ],
    "completion": {
        "dialogue": [
            "Outstanding preparation, Commander!",
            "You have earned the LunArk Cadet Wings badge.",
            "Base control is now in your hands. Good luck!",
        ],
        "expression": 3,
        "badge_title": "LunArk Cadet Wings",
    },
    "glossary": [
        {
            "term": "Helium-3",
            "definition": "A rare gas on the Moon used for clean nuclear fusion.",
            "verify": True,
        },
        {
            "term": "Regolith",
            "definition": "Fine lunar soil that shields buildings from deadly space radiation.",
            "verify": True,
        },
        {
            "term": "Solar Flare",
            "definition": "A powerful burst of high-energy radiation released by the Sun.",
            "verify": True,
        },
        {
            "term": "Micrometeorite",
            "definition": "A tiny space rock travelling faster than a bullet.",
            "verify": True,
        },
        {
            "term": "Fuel Cell",
            "definition": "A clean generator joining hydrogen and oxygen into electricity and water.",
            "verify": True,
        },
        {
            "term": "Nuclear Plant",
            "definition": "A fission power station providing massive, continuous electricity day and night.",
            "verify": True,
        },
        {
            "term": "Lunar Night",
            "definition": "A freezing two-week dark period on the Moon without sunlight.",
            "verify": True,
        },
        {
            "term": "Photovoltaics",
            "definition": "Special panels that convert natural sunlight directly into electrical power.",
            "verify": True,
        },
    ],
}


def load_tutorial() -> dict[str, Any]:
    """Load tutorial script and science glossary with fallback."""
    return load_json_file("tutorial.json", DEFAULT_TUTORIAL)
