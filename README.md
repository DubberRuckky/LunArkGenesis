# LunArk: Genesis

<p align="center">
  <img src="https://github.com/DubberRuckky/LunArkGenesis/blob/main/img/logo/logo.png" width="512" height="512" alt="Logo">
</p>

> A retro pixel-art Moon-base management game for ages 7–12, built by Team LunArk for the **NASA Space Apps Challenge 2026** (48 hours).

In *LunArk: Genesis*, you are the commander of a brand-new lunar base on the Moon! Build habitats, generate clean power, manage your budget, and keep your astronaut crew happy and healthy. Can you complete the scientific research mission and survive three lunar days and nights?

```
+-----------------------------------------------------------------------+
|  [SCREENSHOT PLACEHOLDER: 480x270 Pixel Art Canvas with Lunar Base]   |
+-----------------------------------------------------------------------+
```

---

## 30-Second Quick Start

### Requirements
- **Python**: **3.10** or newer
- **Engine**: `pygame-ce==2.5.8` (community edition of Pygame)

### Installation & Launch

1. **Navigate into the folder**:
   ```bash
   cd LunArkGenesis
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the game**:
   - **Linux / macOS**:
     ```bash
     python3 main.py
     ```
   - **Windows**:
     ```powershell
     python main.py
     ```

4. **Fast Developer Launch**:
   - Skip startup splash cards:
     ```bash
     python main.py --skip-startup
     ```
   - Enable debug shortcuts (F4 for Win, F5 for Lose, F3 for indicators/placeholders):
     ```bash
     python main.py --skip-startup --debug
     ```

> [!TIP]
> **Stuck in Fullscreen?**
> Press **`F11`** at any time from any screen to instantly toggle between Fullscreen and Windowed mode. Press **`Esc`** in menus to go back, or click **Quit** on the Title Screen.

---

## Controls & Keybindings

| Input | Context | Action |
| :--- | :--- | :--- |
| **Any Key / Click** | Startup Sequence | Skip current logo card |
| **Esc** | Startup Sequence | Skip startup cards straight to Title Screen |
| **Esc** | In-Game | Open Pause Menu / Close Submenus |
| **Space** | In-Game | Pause or resume simulation time |
| **1 / 2 / 3 / 4** | In-Game | Set simulation speed to 1x, 2x, 4x, or 8x |
| **A / D or Left / Right Arrows**| World View | Pan camera left and right across lunar landscape |
| **Middle Mouse Drag** | World View | Pan camera smoothly across the lunar surface |
| **Left Click** | World / Build Tray | Select building card, place module, click buttons |
| **Right Click / Esc** | Placement | Cancel active building placement ghost |
| **F11** | Everywhere | Toggle Fullscreen / Windowed display |
| **F3** | Everywhere | Toggle Diagnostic Overlay |
| **F4** | In-Game (`--debug` only) | Instantly trigger Victory screen |
| **F5** | In-Game (`--debug` only) | Instantly trigger Defeat screen |

---

## How to Play (Astronaut Cadet Guide)

As Outpost Commander, your job is to keep the base running smoothly and achieve humanity's exploration mission.

### Your Goal
1. Complete **Planet Stats** scientific research (reach 100% progress).
2. Survive **3 full lunar day-and-night cycles** (each cycle is 180 seconds of day and 180 seconds of night).

### The Five Indicator Bars
Look at the top of the screen to monitor your base:
1. **Energy** (Yellow): Power stored in your batteries. Buildings use power every second. If Energy stays at 0 for 15 seconds, the base shuts down and you lose!
2. **Science** (Blue): Research points collected by your laboratories. Needed to unlock advanced buildings and complete the Planet Stats mission.
3. **Boredom** (Purple): How restless your crew feels (0 to 100). Keep boredom low with Gyms, Cafes, and Restaurants. If Boredom stays at 100 for 20 seconds, the crew gives up and you lose!
4. **Revenue** (Green): Money you earn from datacentres and mining. Spend revenue to construct new buildings, shield modules, and repair damage.
5. **Event Bar** (Red): The risk of major emergencies. Fills up faster when the crew is bored, and drains when the crew is happy. When it fills completely, a major event occurs!

### Day and Night on the Moon
- **Daylight (180 ticks)**: The Sun shines brightly. Solar Arrays produce plentiful clean Energy.
- **Night (180 ticks)**: The Moon plunges into total darkness. Solar panels stop working completely, and base life support heaters draw extra power. Be sure to build Fuel Cells and store enough power before dusk!

### Building Categories
- **Habitat**: Houses your crew (required for base operations).
- **Generator**: Fuel Cell Generator, Solar Array, Nuclear Plant.
- **Cashflow**: Datacentre, Precious Metal Mining, Helium-3 Extraction.
- **Activity**: Gym, Cafe, Restaurant.
- **Science**: Lab, Land Research, Planet Stats.

---

## Where to Edit

Every number, cost, threshold, timing, and word lives in JSON files inside `game/data/` so you can tune the game without touching Python code!

| What you want to change | File to edit | Key fields / Description |
| :--- | :--- | :--- |
| **Tick rate & speeds** | `game/data/balance.json` | `tick_rate`, `warp_speeds` |
| **Day & night length** | `game/data/balance.json` | `cycle.day_ticks`, `cycle.night_ticks` |
| **Starting indicators & limits**| `game/data/balance.json` | `indicators.energy`, `indicators.boredom`, etc. |
| **Lose timers (15s & 20s)** | `game/data/balance.json` | `lose_conditions.energy_zero_ticks_limit` |
| **Grace & recovery times** | `game/data/balance.json` | `grace_and_recovery.start_grace_period_ticks` |
| **Building costs & stats** | `game/data/buildings.json` | Cost, power use, footprints, revenue, unlocks |
| **On-screen words & hints** | `game/data/text.json` | Strings for menus, HUD, win/lose, science facts |
| **Bar colors & night tint** | `game/data/theme.json` | Bar colors, alert colors, dark blue night tint |
| **Hazard events & chances** | `game/data/events.json` | Solar flare, micrometeorite, dust damage values |
| **Surface terrain & obstacles**| `game/data/map.json` | Boulder positions, crater layout, start column |
| **Tutorial guide steps** | `game/data/tutorial.json` | Intro script and step requirements |
| **Player settings & display** | `saves/settings.json` | Resolution, fullscreen, FPS cap, VSync |

---

## 10-Stage Project Plan

### Core Gameplay
1. **Stage 1 — Foundation update**: Clean JSON data layer (`balance.json`, `text.json`, `theme.json`), pure-Python tick clock (1x, 2x, 4x, 8x), stub screens (Game, Pause, Win, Lose), and `--debug` CLI flag.
2. **Stage 2 — Indicators, HUD and time controls**: 5 top indicator bars, warning thresholds, hover explanation text, time control buttons, and F3 debug editor.
3. **Stage 3 — World and building placement**: Side-view 48-column scrolling world, sky & terrain rendering, build tray with 4 category tabs, ghost placement preview, refund demolish tool, and Habitat Pod placement.
4. **Stage 4 — Building catalogue and economy**: All 13 buildings with footprints, energy/revenue/science/boredom outputs, science & revenue unlock checks, and on/off power toggles.
5. **Stage 5 — Day and night**: 180s day / 180s night cycle, solar cutoff, night heating power drain, sunset alert warnings, battery runtime forecast, and smooth night lighting tint.
6. **Stage 6 — Events and challenges**: Event bar hazard trigger, 6 hazards (Solar Flare, Micrometeorite, Dust, Crew Argument, Equipment Failure, Care Package), regolith shielding, cleaning, and repair.
7. **Stage 7 — Goal, win and lose**: Planet Stats research meter, victory upon research completion + 3 cycles survived, loss on 0 energy (15s) or 100 boredom (20s), and debriefing screens with helpful tips.

### Quality of Life
8. **Stage 8 — Intro and tutorial**: Lieutenant mentor dialogue, player naming ("Commander"), 6-step guided tutorial with UI pulsing highlights, and in-game science glossary.
9. **Stage 9 — Settings, pause, save and load**: Full pause menu, audio volume sliders, dawn autosave, and 3-slot versioned JSON save/load system.
10. **Stage 10 — Polish, audio hooks, accessibility**: Building placement animations, floating resource text, modular audio manager, high-contrast mode, simulation tuning tool (`tools/simulate.py`), and documentation.

---

## Project Structure

```
LunArkGenesis/
├── main.py                  # Application entry point (--skip-startup, --debug)
├── requirements.txt         # Runtime dependencies (pygame-ce)
├── requirements-dev.txt     # Test dependencies (pytest)
├── .gitignore               # Ignores saves, cache, pyc
├── PROGRESS.md              # Live stage tracker and tuning notes
├── AI_DISCLOSURE.md         # Detailed development timeline and AI disclosure
├── README.md                # Documentation, guide, and event log
├── LUNARK_ASSET_GUIDE.md    # Pixel art specifications and priorities
├── fonts/                   # Pixel fonts (DepartureMono-Regular.otf)
├── img/                     # PNG pixel art sprites (procedural fallbacks if absent)
│   ├── logo/                # Brand, Aseprite, and Pygame-CE logos
│   ├── ui/                  # 9-slice frames, buttons, panels
│   ├── icons/               # 16x16 icon sheet
│   ├── terrain/             # 16x16 lunar surface tileset
│   ├── sky/                 # Stars, Sun, Earth, horizon layers
│   ├── buildings/           # 13 building animation strips
│   ├── characters/          # Mentor portrait strip
│   ├── events/              # Event notification art
│   └── fx/                  # Sparks, dust puffs, shields
├── saves/                   # Runtime saves (settings.json, save slots)
├── tests/                   # Pytest suite (pure logic & headless screens)
│   ├── test_restart.py      # Restart command & key group separation tests
│   ├── test_settings.py     # Settings validation & persistence unit tests
│   ├── test_startup_sequence.py # Startup sequence timeline & alpha tests
│   ├── test_clock_and_data.py   # Tick clock & JSON data loader fallback tests
│   └── test_screens.py      # Headless screen transitions & debug triggers
└── game/
    ├── app.py               # Central event loop & screen stack manager
    ├── constants.py         # Static paths, tile/icon maps, and backward-compatible aliases
    ├── assets.py            # AssetManager: loader, 9-slice, procedural placeholders
    ├── logic/               # Pure Python simulation (STRICTLY NO PYGAME IMPORTS)
    │   ├── clock.py         # Fixed-rate TickClock with pause and warp multipliers
    │   ├── data.py          # Safe JSON loader with complete built-in defaults
    │   ├── restart.py       # Safe process restart command generator
    │   ├── settings.py      # Settings schema and validation
    │   └── startup_sequence.py # Intro cards timing and fading state machine
    ├── ui/                  # User interface presentation layer
    │   ├── display.py       # Window scaling, DPI awareness, coordinate conversions
    │   ├── widgets.py       # Reusable 9-slice Button, Panel, Toggle, TextInput
    │   └── screens/         # Screen implementations (Startup, Title, Game, Pause, Win, Lose, Settings)
    └── data/                # Data-driven JSON game balance files
        ├── startup.json     # Startup cards configuration
        ├── balance.json     # Timing, cycles, starting indicators, and lose limits
        ├── text.json        # All on-screen dialogue, hints, and kid-friendly text
        └── theme.json       # Color palettes, night tint, and UI styles
```

---

## Provenance

The foundational display engine, settings menu, 3-card startup sequence, title screen layout, and pixel-art brand logo were developed between **October 15 and October 28, 2026**, prior to the competition.

Every subsequent game feature, simulation logic module, building economy, day/night system, hazard mechanics, tutorial, and documentation addition created during the NASA Space Apps Challenge 2026 (November 14–15, 2026) is logged in the **Event Log** below.

---

## Event Log

- **2026-11-15 (Stage 1 — Foundation Update Completed)**:
  - Audited legacy constants and separated data-driven simulation configuration into `game/data/`.
  - Created `balance.json`, `text.json`, and `theme.json` with kid-friendly text and verified science facts.
  - Built pure-Python data loader (`game/logic/data.py`) with comprehensive built-in defaults.
  - Implemented pure-Python `TickClock` (`game/logic/clock.py`) with pause and 1x/2x/4x/8x warp speeds.
  - Registered stub screens (`GameScreen`, `PauseScreen`, `WinScreen`, `LoseScreen`) in `game/app.py`.
  - Added `--debug` CLI option to `main.py` enabling F4 (Win) and F5 (Lose) triggers.
  - Updated `LUNARK_ASSET_GUIDE.md` with Stage numbers, priority tags, and art needed list.
  - Created `PROGRESS.md` and `AI_DISCLOSURE.md`.
  - Added unit test suite `tests/test_clock_and_data.py` and headless integration tests `tests/test_screens.py`. All 36 tests passing.
- **2026-11-15 (Stage 2 — Indicators, HUD and Time Controls Completed)**:
  - Implemented 5 indicators in pure-Python `GameState` (`game/logic/state.py`): Energy, Science, Boredom, Revenue, Event.
  - Added warning threshold alerts and automatic warp speed drop to 1x on hazards.
  - Built HUD (`game/ui/hud.py`) with 9-slice bar frames, icon extraction from spritesheet, flashing alerts, and kid-friendly hover tooltips.
  - Built interactive time control buttons and F3 developer debug overlay.
  - Added test suite `tests/test_state_and_hud.py`. All 41 tests passing.
- **2026-11-15 (Stage 3 — World and Building Placement Completed)**:
  - Created `map.json` for 48-column lunar surface, terrain tiles, boulders, and crater center.
  - Built pure-Python `WorldGrid` (`game/logic/world.py`) with placement collision, demolish refund, and Habitat Pod protection.
  - Implemented camera panning (A/D, arrows, middle mouse drag), snapped ghost preview with valid/invalid tints, and building info panel.
  - Built bottom build tray with 4 category tabs and tier cards.
  - Added test suite `tests/test_world_and_placement.py`. All 49 tests passing.
- **2026-11-15 (Stage 4 — Building Catalogue and Economy Completed)**:
  - Created `buildings.json` and `text.json` definitions for all 13 buildings with exact footprints and rates.
  - Built pure-Python economy logic (`game/logic/economy.py`) calculating net resource rates and evaluating unlocks.
  - Integrated interactive on/off power switches on building info panels.
  - Updated `BuildTray` with lock icons and plain-words requirement messages for locked tiers.
  - Updated `LUNARK_ASSET_GUIDE.md` with complete footprints and frame dimensions.
  - Added test suite `tests/test_economy_and_buildings.py`. All 55 tests passing.
- **2026-11-15 (Stage 5 — Day and Night Completed)**:
  - Built pure-Python `LunarClock` (`game/logic/lunar_clock.py`) with 180s day and 180s night progression.
  - Added solar day/night cutoffs, night heating loads, dusk warnings at 30s before sunset, and warp drop to 1x at dusk.
  - Added HUD day/night widget with Sun/Moon icons and battery lifetime forecasting.
  - Added smooth atmospheric night tint and first-time lunar night modal explanation.
  - Added test suite `tests/test_lunar_clock.py`. All 61 tests passing.
- **2026-11-15 (Stage 6 — Events and Challenges Completed)**:
  - Created `events.json` defining 6 events with weighted odds, countdown warnings, and hazard effects.
  - Built pure-Python `EventManager` (`game/logic/events.py`) with start grace period protection, recovery windows, and drop to 1x on warnings.
  - Added regolith shielding, solar dust cleaning, and module breakdown repairs.
  - Updated `LUNARK_ASSET_GUIDE.md` with new FX sprite strip contracts.
  - Added test suite `tests/test_events_and_shielding.py`. All 68 tests passing.
- **2026-11-15 (Stage 7 — Goal, Win and Lose Completed)**:
  - Built pure-Python `ObjectiveManager` (`game/logic/objectives.py`) for Planet Stats research meter, victory evaluation, and failure condition tracking.
  - Enforced victory check: Planet Stats research complete AND 3 full day-night cycles survived.
  - Enforced defeat conditions: Energy stays at 0 for 15 ticks OR Boredom stays at 100 for 20 ticks (with 60-second start grace period immunity).
  - Integrated critical red countdown alert banner under HUD and automatic warp drop to 1x.
  - Implemented mission debriefing `WinScreen` and `LoseScreen` displaying mission statistics, plain-words explanation of cause, and single selected hint.
  - Added test suite `tests/test_objectives.py`. All 74 tests passing.
- **2026-11-15 (Stage 8 — Intro and Tutorial Completed)** *(Claude in Antigravity, continuation)*:
  - Created `game/data/tutorial.json` (welcome, 6 steps, badge, 8-entry science glossary).
  - Built `TutorialManager` (`game/logic/tutorial.py`): name prompt, step progression, skip, restart, training constraints, glossary.
  - Built `IntroScreen` (`game/ui/screens/intro_screen.py`): mentor portrait (4 expressions), dialogue advance, pulsing highlight, name input, Glossary/Skip/Next buttons; `G` key glossary, `Esc` skip.
  - `start_new_game()` now routes through IntroScreen; name stored and passed to GameScreen.
  - `H` key in-game opens glossary via tutorial screen. Added `tests/test_tutorial.py`. All 87 tests passing.
- **2026-11-15 (Stage 9 — Settings, Pause, Save and Load Completed)** *(Claude in Antigravity, continuation)*:
  - Created 3-slot save/load engine (`game/logic/save_load.py`) storing state, indicators, buildings, cycle, and objectives in pure Python.
  - Added audio volume configuration (`audio_master`, `audio_music`, `audio_sfx`) to settings and settings menu.
  - Built `game/audio.py` (`AudioManager`) with volume scaling and safe silent fallbacks; zero pygame imports in `game/logic`.
  - Rebuilt `PauseScreen` with interactive 3-slot save/load picker; wired dawn autosave hook to `LunarClock.on_dawn`.
  - Added test suite `tests/test_save_load.py`. All 92 tests passing.
- **2026-11-15 (Stage 10 — Polish, Audio Hooks, and Accessibility Completed)** *(Claude in Antigravity, continuation)*:
  - Added building placement pop visual animation, floating revenue/science gain texts, and screen shake on meteor hit.
  - Implemented smooth indicator bar interpolation (`display_ratios` lerp) and geometric shape badges for colorblind accessibility.
  - Added toggleable high-contrast HUD mode (`C` key) and full keyboard controls guide overlay (`?` / `/` key).
  - Wired full suite of audio hooks (button click, building placement, demolish, warnings, nightfall, win, lose).
  - Built headless simulation tool (`tools/simulate.py`) for rapid 1000-tick balance analysis.
  - Added test suite `tests/test_polish_and_simulation.py`. All 96 tests passing.
- **Fix Pass — UI Polish, Missing-Art Frames, Dynamic Art Wiring, Auto-Sized Text Boxes, Tutorial Declutter** *(continuation — Gemini Flash in Antigravity)*:
  - Resolved ternary tuple syntax error in `build_tray.py` hover borders and verified every screen draws headless across mouse positions.
  - Re-layered HUD bar drawing (background -> fill -> frame -> icon & badge -> number) and converted frame placeholders to hollow outlines.
  - Wired asset loading for buildings (`img/buildings/<id>.png`), 9-slice panels/buttons/dialogue, cursor, event art, and sparks/dust FX.
  - Replaced hardcoded text truncations with shared `build_text_box` helper and tray card auto-fit logic.
  - Embedded dimmed live game screen behind tutorial walkthrough and aligned prompt text without button collision.
  - All 101 tests passing and headless smoke test clean.
- **Settings Menu Sizing & Multiplatform Launch Scripts** *(continuation — Gemini Flash in Antigravity)*:
  - Redesigned Settings Menu layout into two balanced columns centered cleanly within the 480×270 screen boundaries.
  - Added `SettingsMenu = SettingsScreen` alias, `resize()` method, cadet tips box, and robust text-wrapping & word breaking in `wrap_text_to_width` and `draw_text`.
  - Created Windows CMD batch script `start_game.bat` (`python main.py --skip-startup --debug`) and executable POSIX bash script `start_game.sh` (`python3 main.py`).
  - Added unit test suite `test_settings_menu_sizing_and_wrapping` in `test_screens.py` (102 tests passing).

---

## Changelog History (Pre-Event)

- **Display Settings Flow & Restart Prompt**:
  - Replaced fragile 10-second auto-revert window recreation with an explicit restart confirmation prompt.
  - Categorized settings into Live (`fps_cap`, `show_fps`) and Restart-Needed (`fullscreen`, `resolution`, `integer_scaling`, `vsync`).
  - Added pure-Python command generator (`game/logic/restart.py`) preserving arguments and paths with spaces.
  - Added `--skip-startup` CLI flag in `main.py` allowing fast reboot straight to the Title screen.
  - Implemented "Restart required" modal ("Restart Now" / "Later") and orange "Restart to apply" header reminder.
  - Added desktop resolution support via `extra_resolutions` in settings validation.
  - Added `pygame.VIDEORESIZE` event handling and window bounds clamping against desktop dimensions.
  - Preserved live F11 fullscreen toggling without discarding pending restart settings.
- **Startup Sequence (3-Card Chain)**:
  - Replaced single splash screen with a 3-card introductory sequence: Team (`logo.png`), Art (`aseprite.png`), and Engine (`pygame_ce.png`).
  - Implemented pure-Python sequence timeline logic (`game/logic/startup_sequence.py`) with zero pygame dependencies.
  - Added data-driven configuration (`game/data/startup.json`) with robust built-in fallbacks.
  - Supported per-card scaling modes (`integer` for pixel art, `fit` for non-pixel logos up to 120×72 box).
  - Added single-card skip (any key/click) and full-sequence skip (`Esc`).
  - Added `STARTUP_ENABLED` toggle in `game/constants.py` for instant developer booting.
- **Typography Update (Departure Mono)**:
  - Integrated Departure Mono by Helena Zhang (`fonts/DepartureMono-Regular.otf`) under SIL Open Font License 1.1.
  - Implemented the strict multiple-of-11 rule (sizes 11, 22, 33) across all UI elements.
  - Expanded settings menu container and aligned option selectors cleanly.
- **Asset Integration, Icons, UI Formatting & Grid Expansion (November 2026)**:
  - Added welcome dialog and `.venv` setup scripts for Windows (`start_game.bat`) and Linux/macOS (`start_game.sh`).
  - Wired in-memory texture loading with support for vertical 9-slice button sheets (`(24, 96)`) and memory-scaled 2x2 building footprints without changing source files.
  - Replaced solid placeholder boxes with crisp 16x16 procedural vector pixel icons and terrain tiles.
  - Resolved UI text collisions across the building inspection panel, placement ghost hints, HUD readouts, and build tray lock banners.
  - Expanded world surface to 72 columns (50% increase in building area) and enabled clearing obstacle boulders via the Demolish tool.

---

## AI Disclosure

- **Code & Test Suite**: Developed with AI pair programming assistance (**Google Antigravity**). Reviewed, verified, and adapted by Team LunArk for clean architecture, type safety, and didactic clarity.
- **Pixel Art & Visuals**: Hand-drawn by the game designer in **Aseprite**.

---

## Credits & License

### Credits
- **Game Design & Pixel Art**: LunArk Team (created with Aseprite).
- **Font**: **Departure Mono** by Helena Zhang ([https://departuremono.com](https://departuremono.com)), licensed under the **SIL Open Font License 1.1**. Font files and license text are preserved in `fonts/`. Designed on an 11 px grid; strictly rendered in multiples of 11 (11, 22, 33) with antialiasing disabled for authentic pixel-art fidelity.
- **Attribution Logos**:
  - **Aseprite**: The Aseprite logo and wordmark are trademarks of Igara Studio S.A.
  - **Pygame Community Edition (Pygame-CE)**: The Pygame-CE logo is maintained by the Pygame Community Edition project.

### License
Created for the **NASA Space Apps Challenge 2026**.
Released under the **GNU General Public License v3.0** (`GPL-3.0`).
