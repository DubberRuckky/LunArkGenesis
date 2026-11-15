# AI Disclosure — LunArk: Genesis

This document records all AI assistance used in the development of *LunArk: Genesis* for the **NASA Space Apps Challenge 2026**.

All code was developed in collaboration with **Google Antigravity**. Every line of code, test case, and JSON configuration was designed, reviewed, and verified to ensure clean architecture, type annotations, zero-external-pygame logic boundaries, and age-appropriate content for players aged 7–12.

All pixel art and visual illustrations were created by human artists in **Aseprite**.

## Development Timeline & Event Log

- **2026-10-15 to 2026-10-28 (Pre-Event Foundation)**:
  - Developed initial display scaling engine, Windows DPI awareness, and integer letterboxing.
  - Built pure-Python settings validation and restart modal manager.
  - Designed 3-card startup sequence and runtime placeholder asset fallback system.
  - Created initial pixel-art brand logo in Aseprite.

- **2026-11-15 (Stage 1 — Foundation Update)**:
  - Audited code against the 10-stage specification and moved gameplay constants to JSON.
  - Implemented pure-Python data loader (`game/logic/data.py`) with complete built-in fallbacks.
  - Created `balance.json`, `text.json`, and `theme.json` in `game/data/`.
  - Built pure-Python `TickClock` (`game/logic/clock.py`) supporting pause and 1x/2x/4x/8x speeds.
  - Created and registered stub screens (`GameScreen`, `PauseScreen`, `WinScreen`, `LoseScreen`).
  - Added `--debug` CLI argument to `main.py` enabling F4 (Win) and F5 (Lose) triggers.
  - Updated `LUNARK_ASSET_GUIDE.md` with Stage numbers, priority tags, and art needed list.
  - Added unit test suite `test_clock_and_data.py` and integration tests `test_screens.py`.

- **2026-11-15 (Stage 2 — Indicators, HUD and Time Controls)**:
  - Built pure-Python `GameState` (`game/logic/state.py`) with 5 indicator bars, bounds clamping, natural boredom rise, late-game bump, and event risk escalation.
  - Implemented warning threshold detection and hook triggering automatic warp drop to 1x.
  - Created modular top HUD (`game/ui/hud.py`) with 9-slice bar frames, icon extraction from spritesheet, and flashing warning states.
  - Added kid-friendly hover tooltips explaining indicator purpose and why values change.
  - Built interactive time control buttons (Pause, 1x, 2x, 4x, 8x) and F3 debug tuning overlay.
  - Added comprehensive test suite `tests/test_state_and_hud.py` (41 passing tests).

- **2026-11-15 (Stage 3 — World and Building Placement)**:
  - Created `map.json` defining 48-column surface grid, surface row 10, boulder at col 8, and crater at cols 30-32.
  - Implemented pure-Python `WorldGrid` (`game/logic/world.py`) validating bounds, obstacle collisions, overlaps, funds, and demolish refunds.
  - Pre-placed initial Habitat Pod at column 20 with demolition protection.
  - Built 50px bottom Build Tray (`game/ui/build_tray.py`) with 4 category tabs and 3 tier cards per category.
  - Added camera panning (A/D, arrows, middle mouse drag) and snapped placement ghost with COLOR_VALID/INVALID tint.
  - Built building inspection panel and unit test suite `tests/test_world_and_placement.py` (49 passing tests).

- **2026-11-15 (Stage 4 — Building Catalogue and Economy)**:
  - Created `buildings.json` specifying footprints, costs, production/consumption rates, and science/revenue prerequisites for all 13 buildings.
  - Implemented pure-Python building economy simulation (`game/logic/economy.py`) with support for on/off power states, broken state hooks, and solar day/night behavior.
  - Updated `BuildTray` with lock icons and plain-words requirement messages for locked tiers.
  - Added interactive on/off power toggle button to building info panel.
  - Documented complete building footprints and dynamic animation frame rules in `LUNARK_ASSET_GUIDE.md`.
  - Added unit test suite `tests/test_economy_and_buildings.py` (55 passing tests).

- **2026-11-15 (Stage 5 — Day and Night Cycle)**:
  - Built pure-Python `LunarClock` (`game/logic/lunar_clock.py`) managing 180s day and 180s night progression across 3 cycles.
  - Implemented solar output day/night cutoff, dawn/dusk ramping, and night heating power load (-3 Energy/tick).
  - Built dusk alert warning triggering 30 seconds before nightfall and automatic warp speed drop to 1x at dusk.
  - Added HUD day/night phase indicator (Sun/Moon icons and progress strip) and battery lifetime forecast.
  - Rendered smooth atmospheric darkness tint using `theme.json` night palette and created first-time lunar night explanation modal.
  - Added unit test suite `tests/test_lunar_clock.py` (61 passing tests).

- **2026-11-15 (Stage 6 — Events and Challenges)**:
  - Created `events.json` defining the 6 core hazards: Solar Flare, Micrometeorite, Lunar Dust, Crew Argument, Equipment Failure, and Care Package.
  - Implemented pure-Python `EventManager` (`game/logic/events.py`) managing countdown warnings, start grace period protection, post-major-event recovery windows, and automatic warp drop to 1x.
  - Added regolith shielding system mitigating radiation damage, dust accumulation on solar arrays, dust cleaning, and module repairs.
  - Updated `LUNARK_ASSET_GUIDE.md` with specifications for regolith mounds, dust overlays, care packages, and meteor streaks.
  - Added unit test suite `tests/test_events_and_shielding.py` (68 passing tests).

- **2026-11-15 (Stage 7 — Goal, Win and Lose)**:
  - Built pure-Python `ObjectiveManager` (`game/logic/objectives.py`) managing Planet Stats research progress, win conditions (complete research AND survive 3 lunar cycles), and defeat conditions (15 ticks at 0 Energy or 20 ticks at 100 Boredom).
  - Implemented 60-second start grace period immunity and critical countdown alert banners with warp drop to 1x.
  - Upgraded `WinScreen` and `LoseScreen` with comprehensive mission debriefing, statistics (cycles, buildings, science), single kid-friendly advice hint from `text.json`, and Play Again / Back to Title navigation.
  - Added unit test suite `tests/test_objectives.py` and screen integration tests (74 passing tests).

- **2026-11-15 (Stage 8 — Intro and Tutorial)** *(continuation — written by Claude in Antigravity after previous model)*:
  - Created `game/data/tutorial.json` with welcome dialogue, 6 guided steps, completion badge, and science glossary (8 entries, all `"verify": true`).
  - Added `load_tutorial()` to `game/logic/data.py` with built-in fallback.
  - Built pure-Python `TutorialManager` (`game/logic/tutorial.py`): name prompt (max 12 chars), 6-step progression, skip, restart, training constraints (clamps Energy ≥ 25, Boredom ≤ 50, Revenue ≥ 50), glossary access.
  - Built `IntroScreen` (`game/ui/screens/intro_screen.py`): mentor portrait (4 expressions from sprite strip), multi-line dialogue with line-by-line advance, pulsing highlight overlay on target UI region, `TextInput` name box, Next/Skip/Glossary buttons, `G` key glossary, `Esc` to skip, `Space/Enter` to advance.
  - Registered `IntroScreen` in `app.py`; `start_new_game()` now routes through intro; `start_game_with_name()` stores Commander name and launches `GameScreen`.
  - `GameScreen` stores `player_name` from app; `H` key opens glossary via tutorial screen.
  - Added `tests/test_tutorial.py` (13 tests). All 87 tests passing.

- **2026-11-15 (Stage 9 — Settings, Pause, Save and Load)** *(continuation — written by Claude in Antigravity after previous model)*:
  - Implemented 3-slot save and load engine (`game/logic/save_load.py`): stores version, player name, play time, indicators, buildings, cycle, clock, and objectives; pure Python with zero pygame dependencies.
  - Added `audio_master`, `audio_music`, `audio_sfx` volume settings (0-10) with validation in `game/logic/settings.py` and UI OptionSelectors in `game/ui/screens/settings_menu.py`.
  - Created `game/audio.py` implementing `AudioManager` with silent fallbacks, volume scaling, and channel isolation; created pure-Python stub in `game/logic/audio.py`.
  - Rebuilt `PauseScreen` (`game/ui/screens/pause_screen.py`) with 5 options: Resume, Settings, Save Game, Load Game, Quit to Title, with an interactive 3-slot picker overlay displaying metadata.
  - Added play time tracking and automatic dawn autosave hook to `GameScreen`; updated `TitleScreen` Continue button to check `any_save_exists()`.
  - Added unit test suite `tests/test_save_load.py` (5 tests). All 92 tests passing.

- **2026-11-15 (Stage 10 — Polish, Audio Hooks, and Accessibility)** *(continuation — written by Claude in Antigravity after previous model)*:
  - Added building placement pop animation with expanding cyan outline and `audio.play("build")` audio hook.
  - Implemented floating `+$N` revenue and `+N Sci` science income text indicators in `GameScreen`.
  - Built camera screen shake feedback on micrometeorite event impact and wired `audio.play("warning")` / `audio.play("flare")`.
  - Added smooth bar interpolation (`display_ratios` lerp) in HUD, distinct geometric badge symbols for colorblind accessibility, and toggleable high-contrast HUD mode (`C` key).
  - Built interactive keyboard shortcuts guide overlay (`?` / `/` key) and verified all click targets meet or exceed 16×16px.
  - Created headless balance simulation tool (`tools/simulate.py`) running 1000 ticks with zero pygame dependencies for economy tuning.
  - Added unit test suite `tests/test_polish_and_simulation.py` (4 tests). All 96 tests passing.

- **2026-11-15 (Fix Pass — UI Polish, Missing-Art Frames, Dynamic Art Wiring, Auto-Sized Text Boxes, Tutorial Declutter)** *(continuation — written by Gemini Flash in Antigravity)*:
  - Fixed tuple nesting bug in `build_tray.py` hover border color ternaries causing crash; added comprehensive headless screen draw test.
  - Made missing-art frame placeholders transparent-center outlines, corrected HUD bar draw layering (bg -> fill -> frame -> icon -> text), and shifted colorblind badges clear of bars.
  - Wired full asset loading for buildings, 9-slice UI textures (`panel`, `button`, `dialogue_box`, `toggle`, `next_arrow`, `cursor`), event illustrations, and FX sparks/dust with code fallbacks.
  - Removed all hard character-count truncations and implemented shared `build_text_box` helper and card name auto-fitting ensuring all building names fit in tray cards.
  - Integrated live game background under dimmed tutorial overlay and positioned "SPACE or ENTER" hint without button overlap.
  - Added unit tests across all 5 fix tasks (now 101 tests passing). Headless smoke test clean.

- **2026-11-15 (Settings Menu Sizing & Multiplatform Launch Scripts)** *(continuation — written by Gemini Flash in Antigravity)*:
  - Resized and centered Settings Menu into a balanced two-column layout fitting completely within 480×270 screen boundaries.
  - Added `SettingsMenu = SettingsScreen` alias, `resize()` method, age 7–12 cadet tips box, and robust text-wrapping & word breaking in `wrap_text_to_width` and `draw_text`.
  - Created `start_game.bat` using CMD commands (`python main.py --skip-startup --debug`) and executable `start_game.sh` (`python3 main.py`).
  - Added unit test suite `test_settings_menu_sizing_and_wrapping` in `test_screens.py` (all 102 tests passing).

- **2026-11-15 (Asset Integration, Icon Fixes, Text Formatting & World Grid Expansion)** *(continuation — written by Antigravity)*:
  - Updated both `start_game.bat` and `start_game.sh` with welcome dialogues, automated `.venv` creation, and dependency installation.
  - Wired in-memory loading and scaling for textures in `img/` (supporting vertical button sheets `(24, 96)` and scaling 48x48 art into 2x2 grid footprints without touching source files on disk).
  - Implemented crisp procedural 16x16 vector pixel fallback icons and terrain tiles across all 24 indices with zero magenta box artifacts.
  - Expanded building info panel from 260px to 310px, eliminating button text collisions and improving action labels ("Repair $25", "Clean $15", "Shield $30", "Protected").
  - Clamped placement ghost hint above HUD and within screen boundaries; moved build tray lock banners cleanly above the tray.
  - Increased placeable world area by 50% (72 columns, 1152px wide world with 2.4 screens of panning) and enabled clearing obstacle boulders via the Demolish tool.
  - Added unit tests in `test_polish_and_simulation.py` (105 tests passing, headless smoke test 100% clean).
