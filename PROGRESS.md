# LunArk: Genesis — Project Progress Tracker

## Current Status
- **Current Stage**: Stage 10 - Polish, audio hooks and accessibility (quality of life)
- **Status**: Completed (96 unit & integration tests passing)
- **Next Stage**: All 10 Stages Completed — Ready for Team Review & Event Presentation!

## Stage Roadmap Overview
- [x] **Stage 1**: Foundation update (Audit, Data Layer, Tick Clock, Stub Screens, Logs)
- [x] **Stage 2**: Indicators, HUD and time controls (5 Bars, Warnings, Tooltips, Speed, F3 Debug)
- [x] **Stage 3**: World and building placement (48-col World, Camera Panning, Ghost Preview, Build Tray, Demolish)
- [x] **Stage 4**: Building catalogue and economy (13 Buildings, Rates, Unlocks, On/Off Switch)
- [x] **Stage 5**: Day and night (180s Cycle, Solar Cutoff, Heating Load, Dusk Warning, Night Tint)
- [x] **Stage 6**: Events and challenges (6 Hazards, Warning Countdown, Shielding, Cleaning, Repairs)
- [x] **Stage 7**: Goal, win and lose (Planet Stats Research, 3-Cycle Victory, 15s/20s Defeat, Debrief Hints)
- [x] **Stage 8**: Intro and tutorial (IntroScreen, 6-step walkthrough, name prompt, glossary, training constraints, H=help)
- [x] **Stage 9**: Settings, pause, save and load (3 Save Slots, Pause Menu, Audio Volume Sliders, Dawn Autosave)
- [x] **Stage 10**: Polish, audio hooks, accessibility, simulation (Pops, Floating Texts, Screen Shake, Lerp Bars, Audio Hooks, Headless Tool)

## Proposed Economy Balance Numbers for Tuning (`game/data/buildings.json`)

| Building ID | Name | Cat | Tier | Size | Cost | Power/s | Rev/s | Sci/s | Boredom/s | Unlock Req |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `habitat_pod` | Habitat Pod | Hab | 1 | 4×3 | $0 | -1.0 | 0 | 0 | 0 | Free (Start) |
| `fuel_cell` | Fuel Cell | Gen | 1 | 2×2 | $40 | +5.0 | 0 | 0 | 0 | Free |
| `solar_array` | Solar Array | Gen | 2 | 3×1 | $75 | +10.0* | 0 | 0 | 0 | 20 Sci, $60 Rev |
| `nuclear_plant`| Nuclear Plant | Gen | 3 | 3×3 | $180| +25.0 | 0 | 0 | 0 | 60 Sci, $140 Rev |
| `datacentre` | Datacentre | Cash | 1 | 2×2 | $50 | -2.0 | +4.0 | 0 | 0 | Free |
| `metal_mining` | Metal Mining | Cash | 2 | 3×2 | $90 | -4.0 | +9.0 | 0 | 0 | 25 Sci, $70 Rev |
| `helium3_extraction`| Helium-3 | Cash | 3 | 3×3 | $160| -8.0 | +18.0| 0 | 0 | 55 Sci, $120 Rev |
| `gym` | Lunar Gym | Act | 1 | 2×2 | $35 | -1.0 | 0 | 0 | -0.3 | Free |
| `cafe` | Base Cafe | Act | 2 | 2×2 | $65 | -2.0 | 0 | 0 | -0.6 | 15 Sci, $50 Rev |
| `restaurant` | Restaurant | Act | 3 | 3×2 | $120| -4.0 | 0 | 0 | -1.2 | 45 Sci, $100 Rev |
| `lab` | Research Lab | Sci | 1 | 2×2 | $45 | -2.0 | 0 | +1.0 | 0 | Free |
| `land_research`| Land Survey | Sci | 2 | 3×2 | $80 | -4.0 | 0 | +2.5 | 0 | 20 Sci, $60 Rev |
| `planet_stats` | Planet Stats | Sci | 3 | 3×3 | $200| -6.0 | 0 | +5.0 | 0 | 50 Sci, $150 Rev |

*\* Solar Array output stops at night (0 Power).*

## Placeholders Still in Use
- All gameplay visuals currently utilize runtime procedural placeholders:
  - Sky starfield & parallax horizons (`img/sky/`)
  - Terrain tileset (`img/terrain/tileset.png`)
  - Shared icons sheet (`img/icons/icons.png`)
  - UI 9-slice elements: `bar_frame.png`, `panel.png`, `button.png`, `dialogue_box.png`
  - Victory and Defeat backdrops (`end_win.png`, `end_lose.png`)
  - Building sprite strips (`img/buildings/*.png`)

## Art Needed Now
1. `img/ui/bar_frame.png` (12×10, 3px corner) for HUD indicator bars.
2. `img/icons/icons.png` (Row 0: 0–4 indicator icons, 10 warning, 16–18 time control icons).
3. `img/terrain/tileset.png` (Row 0: surface regolith and obstacles).

## Notes & Tuning Points
- Tick rate is fixed at 1.0 second per tick at 1x speed.
- Day and night length set to 180 ticks each in `game/data/balance.json`.
- Lose thresholds: 15 ticks at 0 Energy, 20 ticks at 100 Boredom.
- Existing folders `__pycache__/` and `saves/settings.json` exist and were left untouched.
