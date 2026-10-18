# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Fixed constants for LunArk: Genesis.

All magic numbers, colors, file paths, and lookup tables live here
so they are easy to find and change in one place.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# ROOT_DIR is the project root (parent of game/)
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
IMG_DIR: Path = ROOT_DIR / "img"
FONT_DIR: Path = ROOT_DIR / "fonts"
SAVE_DIR: Path = ROOT_DIR / "saves"
DATA_DIR: Path = ROOT_DIR / "game" / "data"

SETTINGS_FILE: Path = SAVE_DIR / "settings.json"
SAVEGAME_FILE: Path = SAVE_DIR / "savegame.json"
STARTUP_FILE: Path = DATA_DIR / "startup.json"

# Font: Departure Mono by Helena Zhang (SIL Open Font License 1.1)
# Designed on an 11 px grid. For pixel-perfect rendering with crisp, unblurred edges,
# ONLY use sizes that are integer multiples of 11 (11, 22, 33). At size 11, each glyph
# is 7 px wide and ~14 px tall (capitals 8 px high). Antialiasing is always False.
FONT_NAME: str = "DepartureMono-Regular.otf"
FONT_SIZE_SMALL: int = 11
FONT_SIZE_MEDIUM: int = 11
FONT_SIZE_LARGE: int = 22
FONT_SIZE_TITLE: int = 33

# ---------------------------------------------------------------------------
# Display & Canvas
# ---------------------------------------------------------------------------
INTERNAL_WIDTH: int = 480
INTERNAL_HEIGHT: int = 270
CANVAS_W: int = INTERNAL_WIDTH
CANVAS_H: int = INTERNAL_HEIGHT
TILE_SIZE: int = 16

AVAILABLE_RESOLUTIONS: list[tuple[int, int]] = [
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
]
DEFAULT_RESOLUTION: tuple[int, int] = (1280, 720)

FPS_OPTIONS: list[int] = [30, 60, 120, 144, 0]  # 0 means Unlimited
DEFAULT_FPS: int = 60

# ---------------------------------------------------------------------------
# World & Grid
# ---------------------------------------------------------------------------
WORLD_COLS: int = 48  # 48 cols * 16 px = 768 px wide world
UNDERGROUND_ROWS: int = 4
SURFACE_ROW: int = 10  # Row index where ground surface sits in the world

# ---------------------------------------------------------------------------
# Timing & Durations (seconds / ticks)
# ---------------------------------------------------------------------------
SPLASH_FADE_IN: float = 0.5
SPLASH_HOLD: float = 1.5
SPLASH_FADE_OUT: float = 1.0

# Startup sequence configuration
STARTUP_ENABLED: bool = True  # If False, skips straight to Title screen for fast dev
STARTUP_GAP_SECONDS: float = 0.15  # Black gap between consecutive startup cards

SETTINGS_REVERT_SECONDS: int = 10

DAY_TICKS: int = 180
NIGHT_TICKS: int = 180
FIXED_TICK_RATE: float = 1.0  # 1 logic tick = 1 second at 1x speed

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
COLOR_BLACK: tuple[int, int, int] = (0, 0, 0)
COLOR_WHITE: tuple[int, int, int] = (255, 255, 255)
COLOR_DARK_GREY: tuple[int, int, int] = (40, 40, 40)
COLOR_MID_GREY: tuple[int, int, int] = (100, 100, 100)
COLOR_LIGHT_GREY: tuple[int, int, int] = (180, 180, 180)

# Five bars accent colors
COLOR_ENERGY: tuple[int, int, int] = (255, 220, 50)     # yellow
COLOR_SCIENCE: tuple[int, int, int] = (80, 180, 255)    # blue
COLOR_BOREDOM: tuple[int, int, int] = (200, 80, 200)    # purple
COLOR_REVENUE: tuple[int, int, int] = (80, 220, 80)     # green
COLOR_EVENT: tuple[int, int, int] = (220, 60, 60)       # red

# Placement ghost colors
COLOR_VALID: tuple[int, int, int] = (80, 220, 80)       # green ghost
COLOR_INVALID: tuple[int, int, int] = (220, 60, 60)     # red ghost

# UI & Buttons
COLOR_BUTTON_NORMAL: tuple[int, int, int] = (55, 60, 75)
COLOR_BUTTON_HOVER: tuple[int, int, int] = (75, 80, 100)
COLOR_BUTTON_PRESSED: tuple[int, int, int] = (40, 44, 55)
COLOR_BUTTON_DISABLED: tuple[int, int, int] = (45, 45, 50)
COLOR_BUTTON_BORDER: tuple[int, int, int] = (110, 115, 130)
COLOR_BUTTON_TEXT: tuple[int, int, int] = (230, 230, 230)
COLOR_BUTTON_TEXT_DISABLED: tuple[int, int, int] = (100, 100, 110)

# Panels & Dialogues (RGBA)
COLOR_PANEL_BG: tuple[int, int, int, int] = (20, 22, 32, 225)
COLOR_PANEL_BORDER: tuple[int, int, int] = (90, 95, 115)

COLOR_DIALOGUE_BG: tuple[int, int, int, int] = (14, 16, 24, 235)
COLOR_DIALOGUE_BORDER: tuple[int, int, int] = (100, 110, 140)

COLOR_TOOLTIP_BG: tuple[int, int, int, int] = (12, 14, 20, 240)
COLOR_TOOLTIP_BORDER: tuple[int, int, int] = (120, 125, 150)

COLOR_INPUT_BG: tuple[int, int, int] = (25, 28, 38)
COLOR_INPUT_BORDER: tuple[int, int, int] = (100, 110, 140)
COLOR_INPUT_ACTIVE_BORDER: tuple[int, int, int] = (140, 160, 220)

COLOR_BAR_BG: tuple[int, int, int] = (30, 30, 40)
COLOR_BAR_BORDER: tuple[int, int, int] = (80, 80, 100)

COLOR_TOGGLE_OFF: tuple[int, int, int] = (90, 90, 105)
COLOR_TOGGLE_ON: tuple[int, int, int] = (72, 191, 83)
COLOR_TOGGLE_KNOB: tuple[int, int, int] = (230, 230, 230)

# Sky and Celestial Bodies
COLOR_SKY: tuple[int, int, int] = (8, 8, 12)  # Lunar sky is black
COLOR_GROUND: tuple[int, int, int] = (115, 115, 110)  # Grey regolith
COLOR_STAR: tuple[int, int, int] = (220, 220, 230)
COLOR_SUN: tuple[int, int, int] = (255, 255, 210)
COLOR_EARTH: tuple[int, int, int] = (70, 130, 210)

# Missing asset placeholder color
COLOR_PLACEHOLDER: tuple[int, int, int] = (180, 50, 180)  # Magenta
COLOR_PLACEHOLDER_TEXT: tuple[int, int, int] = (255, 255, 255)

# ---------------------------------------------------------------------------
# Icon index table (img/icons/icons.png: 8 columns, 16x16 each)
# ---------------------------------------------------------------------------
ICON: dict[str, int] = {
    "energy": 0,
    "science": 1,
    "boredom": 2,
    "revenue": 3,
    "event": 4,
    "cat_generator": 5,
    "cat_cashflow": 6,
    "cat_activity": 7,
    "cat_science": 8,
    "cat_habitat": 9,
    "warning": 10,
    "offline": 11,
    "broken": 12,
    "locked": 13,
    "sun": 14,
    "moon": 15,
    "pause": 16,
    "play": 17,
    "warp": 18,
    "settings": 19,
    "close": 20,
    "check": 21,
    "radiation": 22,
    "dig": 23,
}
ICON_SHEET_COLS: int = 8
ICON_SIZE: int = 16

# ---------------------------------------------------------------------------
# Tile index table (img/terrain/tileset.png: 8 columns x 3 rows, 16x16)
# ---------------------------------------------------------------------------
TILE: dict[str, int] = {
    # Row 0: surface tops & obstacles
    "surface_a": 0,
    "surface_b": 1,
    "surface_c": 2,
    "surface_d": 3,
    "crater_left": 4,
    "crater_mid": 5,
    "crater_right": 6,
    "boulder": 7,
    # Row 1: underground regolith, rock, bedrock
    "regolith_a": 8,
    "regolith_b": 9,
    "regolith_c": 10,
    "regolith_d": 11,
    "rock_a": 12,
    "rock_b": 13,
    "bedrock_a": 14,
    "bedrock_b": 15,
    # Row 2: excavated space & borders
    "dugout_a": 16,
    "dugout_b": 17,
    "dugout_c": 18,
    "dugout_d": 19,
    "dugout_top": 20,
    "dugout_left": 21,
    "dugout_right": 22,
    "dugout_bottom": 23,
}
TILE_SHEET_COLS: int = 8

# ---------------------------------------------------------------------------
# Building Categories
# ---------------------------------------------------------------------------
CATEGORY_GENERATOR: str = "generator"
CATEGORY_CASHFLOW: str = "cashflow"
CATEGORY_ACTIVITY: str = "activity"
CATEGORY_SCIENCE: str = "science"
CATEGORY_HABITAT: str = "habitat"

BUILDING_CATEGORIES: list[str] = [
    CATEGORY_GENERATOR,
    CATEGORY_CASHFLOW,
    CATEGORY_ACTIVITY,
    CATEGORY_SCIENCE,
    CATEGORY_HABITAT,
]

# ---------------------------------------------------------------------------
# Asset Paths (relative to IMG_DIR)
# ---------------------------------------------------------------------------
ASSET_PATHS: dict[str, str] = {
    # Logo
    "logo": "logo/logo.png",
    "logo_aseprite": "logo/aseprite.png",
    "logo_pygame_ce": "logo/pygame_ce.png",
    # UI
    "title": "ui/title.png",
    "title_bg": "ui/title_bg.png",
    "panel": "ui/panel.png",
    "button": "ui/button.png",
    "bar_frame": "ui/bar_frame.png",
    "dialogue_box": "ui/dialogue_box.png",
    "toggle": "ui/toggle.png",
    "next_arrow": "ui/next_arrow.png",
    "cursor": "ui/cursor.png",
    "end_win": "ui/end_win.png",
    "end_lose": "ui/end_lose.png",
    # Icons & terrain
    "icons": "icons/icons.png",
    "tileset": "terrain/tileset.png",
    # Sky
    "stars": "sky/stars.png",
    "earth": "sky/earth.png",
    "sun": "sky/sun.png",
    "horizon_far": "sky/horizon_far.png",
    "horizon_near": "sky/horizon_near.png",
    # Characters
    "mentor": "characters/mentor.png",
    "astronaut": "characters/astronaut.png",
    # Cutscene
    "wake_up_1": "cutscene/wake_up_1.png",
    "wake_up_2": "cutscene/wake_up_2.png",
    # FX
    "sparks": "fx/sparks.png",
    "dust_puff": "fx/dust_puff.png",
    # Vehicles
    "lander": "vehicles/lander.png",
    "rover": "vehicles/rover.png",
}

# Nine-slice corner sizes for UI elements
NINE_SLICE_PANEL_CORNER: int = 8
NINE_SLICE_BUTTON_CORNER: int = 8
NINE_SLICE_BAR_CORNER: int = 3
NINE_SLICE_DIALOGUE_CORNER: int = 8

# Warp speeds
WARP_SPEEDS: list[int] = [0, 1, 2, 4, 8]  # 0 = paused
WARP_LABELS: list[str] = ["||", "1x", "2x", "4x", "8x"]
DEFAULT_WARP: int = 1

# Gameplay thresholds
ENERGY_WARNING_THRESHOLD: float = 0.15  # flash bar below 15%
MAX_PLAYER_NAME_LENGTH: int = 12
DEFAULT_PLAYER_NAME: str = "Commander"

# Screen identifiers for Screen Manager
SCREEN_STARTUP: str = "startup"
SCREEN_SPLASH: str = "startup"  # Alias for backward compatibility
SCREEN_TITLE: str = "title"
SCREEN_SETTINGS: str = "settings"
SCREEN_CUTSCENE: str = "cutscene"
SCREEN_PLAY: str = "play"
SCREEN_PAUSE: str = "pause"
SCREEN_END: str = "end"
