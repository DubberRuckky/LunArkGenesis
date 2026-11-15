# LunArk: Genesis — Artist & Asset Guide

This guide is the contract between pixel art assets drawn in Aseprite and the game engine.

The game uses an internal canvas of **480×270** pixels. All sprites are rendered with nearest-neighbor scaling at whole-pixel coordinates (no fractional offsets, no sprite rotation, no smoothing).

---

## Asset Directory Contract

Drop files directly into `img/` or `fonts/` at the exact paths below. The game will automatically detect and load them without requiring any code or JSON changes.

| Path | Stage | Priority | Description | Dimensions (px) | Format / Animation Notes |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `img/logo/logo.png` | 1 | Must-have first | Splash screen logo | 33×33 | Scaled 3× using nearest-neighbor on splash screen |
| `img/logo/aseprite.png` | 1 | Must-have first | Aseprite logo (Card 2) | max 120×72 | Scaled with aspect-preserving smoothscale fit |
| `img/logo/pygame_ce.png` | 1 | Must-have first | Pygame CE logo (Card 3) | max 120×72 | Scaled with aspect-preserving smoothscale fit |
| `img/ui/title.png` | 1 | Must-have first | Title wordmark logo | ~240×60 | Rendered centered on title screen |
| `img/ui/title_bg.png` | 1 | Later | Title background image | 480×270 | Fullscreen menu backdrop |
| `img/ui/panel.png` | 1 | Must-have first | 9-slice panel frame | 24×24 | Corner size: 8px |
| `img/ui/button.png` | 1 | Must-have first | 9-slice button (4 states) | 96×24 | 4 states side by side (24×24 each): normal, hover, pressed, disabled |
| `img/ui/bar_frame.png` | 2 | Must-have first | 9-slice bar frame | 12×10 | Corner size: 3px (bar fill color drawn in code) |
| `img/ui/dialogue_box.png` | 8 | Later | 9-slice dialogue box | 24×24 | Corner size: 8px |
| `img/ui/toggle.png` | 1 | Later | Binary switch states | 48×12 | 2 frames side by side (24×12 each): off, on |
| `img/ui/next_arrow.png` | 8 | Later | Blinking advance prompt | 16×8 | 2 frames side by side (8×8 each) |
| `img/ui/cursor.png` | 10 | Later | Custom mouse cursor | 32×16 | 2 frames (16×16 each): normal, pointing |
| `img/ui/end_win.png` | 7 | Later | Victory screen picture | 480×270 | Fullscreen victory background |
| `img/ui/end_lose.png` | 7 | Later | Defeat screen picture | 480×270 | Fullscreen defeat background |
| `img/icons/icons.png` | 2 | Must-have first | Shared icon spritesheet | 128×48 | 8 columns × 3 rows of 16×16 icons (see index table below) |
| `img/terrain/tileset.png`| 3 | Must-have first | Terrain tilesheet | 128×48 | 8 columns × 3 rows of 16×16 tiles (Row 0 must-have; Rows 1-2 stretch) |
| `img/sky/stars.png` | 3 | Must-have first | Starfield background | 480×270 | Static deep space background |
| `img/sky/earth.png` | 5 | Later | Earth phase strip | Strip of 32×32 | Horizontal strip of Moon-sky Earth phases |
| `img/sky/sun.png` | 5 | Later | Sun sprite strip | Strip of 24×24 | Horizontal strip of Sun illumination |
| `img/sky/horizon_far.png` | 3 | Later | Far parallax horizon | 480×90 | Distant craters and ridges |
| `img/sky/horizon_near.png`| 3 | Later | Near parallax horizon | 480×60 | Near ridges |
| `img/buildings/<id>.png` | 4 | Must-have first | Building animation strip | `(w*16*N) × (h*16)` | Frame 0 = offline; Frames 1..N = running animation |
| `img/characters/mentor.png` | 8 | Later | Mentor portrait strip | 256×64 | 4 expressions (64×64 each): neutral, welcoming, serious, worried |
| `img/characters/astronaut.png`| 10 | Later | Base astronaut sprites | 72×16 | 6 frames (12×16 each): 2 idle, 4 walk cycle |
| `img/cutscene/wake_up_1.png` | 8 | Later | Awakening cutscene art | 480×270 | Intro cutscene full canvas |
| `img/cutscene/wake_up_2.png` | 8 | Later | Awakening cutscene step 2 | 480×270 | Optional secondary cutscene frame |
| `img/events/<event_id>.png` | 6 | Later | Event alert illustration | 96×64 | Solar flare, dust storm, meteorite, etc. |
| `img/fx/sparks.png` | 6 | Later | Malfunction sparks | 48×16 | 3 frames (16×16 each) |
| `img/fx/regolith_mound.png` | 6 | Later | Regolith shielding mound | 48×16 | 3 frames of 16×16 (left, middle, right, tiled across building) |
| `img/fx/dust_overlay.png` | 6 | Later | Solar dust accumulation | 32×16 | 2 frames of 16×16 (light, heavy, tiled across Solar Array) |
| `img/fx/care_package.png` | 6 | Later | Care package cargo pod | 48×16 | 3 frames of 16×16 parachute drop animation |
| `img/fx/meteor.png` | 6 | Later | Micrometeorite streak | 64×16 | 4 frames of 16×16 impact streak |
| `img/fx/dust_puff.png` | 10 | Later | Construction dust puff | 128×16 | 4 frames (32×16 each) |
| `img/vehicles/lander.png` | — | Stretch | Resupply cargo lander | 48×32 | Resupply animation (Stretch goal) |
| `img/vehicles/rover.png` | — | Stretch | Lunar surface rover | 32×16 | Surface exploration (Stretch goal) |
| `fonts/DepartureMono-Regular.otf` | 1 | Must-have first | Departure Mono pixel font | OpenType OTF | Scaled strictly at multiples of 11 (11, 22, 33) |

---

## Icon Sheet Layout (`img/icons/icons.png`)
8 columns of 16×16 icons (row-major order):

- **Row 0 (0–7): Must-have first**
  - `0`: Energy
  - `1`: Science
  - `2`: Boredom
  - `3`: Revenue
  - `4`: Event Meter
  - `5`: Category Generator
  - `6`: Category Cashflow
  - `7`: Category Activity
- **Row 1 (8–15): Must-have first / Later**
  - `8`: Category Science
  - `9`: Category Habitat
  - `10`: Warning / Alert
  - `11`: Offline
  - `12`: Broken / Damaged
  - `13`: Locked
  - `14`: Sun (Daylight)
  - `15`: Moon (Night)
- **Row 2 (16–23): Later & Stretch**
  - `16`: Pause (Must-have)
  - `17`: Play 1x (Must-have)
  - `18`: Warp Speed (Must-have)
  - `19`: Settings Gear
  - `20`: Close (X)
  - `21`: Checkmark
  - `22`: Radiation Shielding
  - `23`: Dig Excavation (**Stretch**)

---

## Terrain Tileset Layout (`img/terrain/tileset.png`)
8 columns of 16×16 tiles (row-major order):

- **Row 0 (0–7): Surface Horizon & Obstacles (Must-have first)**
  - `0–3`: Surface regolith tops (variants a, b, c, d)
  - `4–6`: Crater rims (left rim, center depression, right rim)
  - `7`: Surface boulder / obstacle
- **Row 1 (8–15): Subsurface Strata (Stretch)**
  - `8–11`: Compacted regolith (variants a, b, c, d)
  - `12–13`: Basalt rock layers (a, b)
  - `14–15`: Lunar bedrock (a, b)
- **Row 2 (16–23): Dug-Out Excavated Space (Stretch)**
  - `16–19`: Dug-out pressurized back walls (variants a, b, c, d)
  - `20`: Excavation top ceiling border
  - `21`: Excavation left wall border
  - `22`: Excavation right wall border
  - `23`: Excavation floor border

---

## Auto-Detected Sprite Strips
For buildings, frame size equals `footprint_w * 16` by `footprint_h * 16`.
The engine detects animation frame count dynamically:
$$\text{frames} = \frac{\text{image\_width}}{\text{frame\_width}}$$
- **Frame 0**: Offline / unpowered state.
- **Frames 1..N**: Looping active animation.

### Building Footprints & Dimensions Table

All 13 building sprite strips live in `img/buildings/<id>.png`:

| Building ID | Name | Category | Tier | Footprint (Tiles) | Frame Size (px) | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `habitat_pod` | Habitat Pod | Habitat | 1 | 4×3 | 64×48 | Required for crew life support |
| `fuel_cell` | Fuel Cell Generator | Generator | 1 | 2×2 | 32×32 | Continuous clean power |
| `solar_array` | Solar Array | Generator | 2 | 3×1 | 48×16 | High solar output (stops at night) |
| `nuclear_plant` | Nuclear Plant | Generator | 3 | 3×3 | 48×48 | Massive base power supply |
| `datacentre` | Datacentre | Cashflow | 1 | 2×2 | 32×32 | Telemetry revenue |
| `metal_mining` | Metal Mining | Cashflow | 2 | 3×2 | 48×32 | Regolith mineral income |
| `helium3_extraction` | Helium-3 Mine | Cashflow | 3 | 3×3 | 48×48 | Clean fusion fuel extraction |
| `gym` | Lunar Gym | Activity | 1 | 2×2 | 32×32 | Lowers crew boredom |
| `cafe` | Base Cafe | Activity | 2 | 2×2 | 32×32 | Hot meals and morale |
| `restaurant` | Restaurant | Activity | 3 | 3×2 | 48×32 | Hydroponic dining |
| `lab` | Research Lab | Science | 1 | 2×2 | 32×32 | Produces science points |
| `land_research` | Land Survey | Science | 2 | 3×2 | 48×32 | Planetary geological study |
| `planet_stats` | Planet Stats | Science | 3 | 3×3 | 48×48 | Mission goal observatory |

---

## Art Still Needed (Priority List)

### Priority 1: Must-Have First (Core Gameplay Stages 1–4)
1. `img/ui/bar_frame.png` (12×10, 3px corner) — frame for the 5 HUD indicator bars.
2. `img/ui/panel.png` (24×24, 8px corner) — 9-slice panel for menus and info cards.
3. `img/ui/button.png` (96×24, 4 states of 24×24) — buttons.
4. `img/icons/icons.png` (128×48, 24 icons of 16×16) — indicator, category, warning, and speed icons.
5. `img/terrain/tileset.png` (Row 0: 8 tiles of 16×16) — lunar surface regolith tops, crater rims, and boulders.
6. `img/sky/stars.png` (480×270) — static starfield background.
7. `img/buildings/` (Initial set of 5 core buildings):
   - `habitat_pod.png` (64×48 per frame)
   - `fuel_cell.png` (32×32 per frame)
   - `datacentre.png` (32×32 per frame)
   - `gym.png` (32×32 per frame)
   - `lab.png` (32×32 per frame)

### Priority 2: Later (Stages 5–8)
1. Remaining 8 buildings in `img/buildings/`:
   - `solar_array.png` (48×16 per frame)
   - `nuclear_plant.png` (48×48 per frame)
   - `metal_mining.png` (48×32 per frame)
   - `helium3_extraction.png` (48×48 per frame)
   - `cafe.png` (32×32 per frame)
   - `restaurant.png` (48×32 per frame)
   - `land_research.png` (48×32 per frame)
   - `planet_stats.png` (48×48 per frame)
2. `img/events/` (96×64 each): `solar_flare.png`, `micrometeorite.png`, `dust.png`, `crew_argument.png`, `equipment_failure.png`, `care_package.png`.
3. `img/characters/mentor.png` (256×64, 4 expressions of 64×64).
4. `img/ui/dialogue_box.png` (24×24, 8px corner).
5. `img/ui/end_win.png` & `img/ui/end_lose.png` (480×270).
6. Sky parallax: `img/sky/horizon_far.png` (480×90), `img/sky/horizon_near.png` (480×60), `img/sky/sun.png`, `img/sky/earth.png`.

### Priority 3: Stretch Goals
1. Dig excavation & underground tileset (Rows 1 & 2 of `img/terrain/tileset.png`).
2. Icon slot 23 (`dig`).
3. Vehicles: `img/vehicles/rover.png` (32×16) and `img/vehicles/lander.png` (48×32).
