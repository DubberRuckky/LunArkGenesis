# LunArk: Genesis — Artist & Asset Guide

This guide is the contract between pixel art assets drawn in Aseprite and the game engine.

The game uses an internal canvas of **480×270** pixels. All sprites are rendered with nearest-neighbor scaling at whole-pixel coordinates (no fractional offsets, no sprite rotation, no smoothing).

---

## Asset Directory Contract

Drop files directly into `img/` or `fonts/` at the exact paths below. The game will automatically detect and load them without requiring any code or JSON changes.

| Path | Description | Dimensions (px) | Format / Animation Notes |
| :--- | :--- | :--- | :--- |
| `img/logo/logo.png` | Splash screen logo | 33×33 | Scaled 3× using nearest-neighbor on splash screen |
| `img/ui/title.png` | Title wordmark logo | ~240×60 | Rendered centered on title screen |
| `img/ui/title_bg.png` | Title background image | 480×270 | Fullscreen menu backdrop |
| `img/ui/panel.png` | 9-slice panel frame | 24×24 | Corner size: 8px |
| `img/ui/button.png` | 9-slice button (4 states) | 96×24 | 4 states side by side (24×24 each): normal, hover, pressed, disabled |
| `img/ui/bar_frame.png` | 9-slice bar frame | 12×10 | Corner size: 3px (bar fill color drawn in code) |
| `img/ui/dialogue_box.png` | 9-slice dialogue box | 24×24 | Corner size: 8px |
| `img/ui/toggle.png` | Binary switch states | 48×12 | 2 frames side by side (24×12 each): off, on |
| `img/ui/next_arrow.png` | Blinking advance prompt | 16×8 | 2 frames side by side (8×8 each) |
| `img/ui/cursor.png` | Custom mouse cursor | 32×16 | 2 frames (16×16 each): normal, pointing |
| `img/ui/end_win.png` | Victory screen picture | 480×270 | Fullscreen victory background |
| `img/ui/end_lose.png` | Defeat screen picture | 480×270 | Fullscreen defeat background |
| `img/icons/icons.png` | Shared icon spritesheet | 128×48 | 8 columns × 3 rows of 16×16 icons (see index table below) |
| `img/terrain/tileset.png`| Terrain tilesheet | 128×48 | 8 columns × 3 rows of 16×16 tiles (see index table below) |
| `img/sky/stars.png` | Starfield background | 480×270 | Static deep space background |
| `img/sky/earth.png` | Earth phase strip | Strip of 32×32 | Horizontal strip of Moon-sky Earth phases |
| `img/sky/sun.png` | Sun sprite strip | Strip of 24×24 | Horizontal strip of Sun illumination |
| `img/sky/horizon_far.png` | Far parallax horizon | 480×90 | Distant craters and ridges |
| `img/sky/horizon_near.png`| Near parallax horizon | 480×60 | Near ridges |
| `img/buildings/<id>.png` | Building animation strip | `(w*16*N) × (h*16)` | Frame 0 = offline; Frames 1..N = running animation |
| `img/characters/mentor.png` | Mentor portrait strip | 256×64 | 4 expressions (64×64 each): neutral, welcoming, serious, worried |
| `img/characters/astronaut.png`| Base astronaut sprites | 72×16 | 6 frames (12×16 each): 2 idle, 4 walk cycle |
| `img/cutscene/wake_up_1.png` | Awakening cutscene art | 480×270 | Intro cutscene full canvas |
| `img/cutscene/wake_up_2.png` | Awakening cutscene step 2 | 480×270 | Optional secondary cutscene frame |
| `img/events/<event_id>.png` | Event alert illustration | 96×64 | Solar flare, dust storm, meteorite, etc. |
| `img/fx/sparks.png` | Malfunction sparks | 48×16 | 3 frames (16×16 each) |
| `img/fx/dust_puff.png` | Construction dust puff | 128×16 | 4 frames (32×16 each) |
| `img/vehicles/lander.png` | Resupply cargo lander | 48×32 | Resupply animation |
| `img/vehicles/rover.png` | Lunar surface rover | 32×16 | Surface exploration |
| `fonts/pixel.ttf` | Custom TTF pixel font | Vector TTF | Scaled at sizes 8, 10, 16, 24 |

---

## Icon Sheet Layout (`img/icons/icons.png`)
8 columns of 16×16 icons (row-major order):

- **Row 0 (0–7):**
  - `0`: Energy
  - `1`: Science
  - `2`: Boredom
  - `3`: Revenue
  - `4`: Event Meter
  - `5`: Category Generator
  - `6`: Category Cashflow
  - `7`: Category Activity
- **Row 1 (8–15):**
  - `8`: Category Science
  - `9`: Category Habitat
  - `10`: Warning / Alert
  - `11`: Offline
  - `12`: Broken / Damaged
  - `13`: Locked
  - `14`: Sun (Daylight)
  - `15`: Moon (Night)
- **Row 2 (16–23):**
  - `16`: Pause
  - `17`: Play (1x)
  - `18`: Warp Speed
  - `19`: Settings Gear
  - `20`: Close (X)
  - `21`: Checkmark
  - `22`: Radiation Shielding
  - `23`: Dig Excavation

---

## Terrain Tileset Layout (`img/terrain/tileset.png`)
8 columns of 16×16 tiles (row-major order):

- **Row 0 (0–7): Surface Horizon & Obstacles**
  - `0–3`: Surface regolith tops (variants a, b, c, d)
  - `4–6`: Crater rims (left rim, center depression, right rim)
  - `7`: Surface boulder / obstacle
- **Row 1 (8–15): Subsurface Strata**
  - `8–11`: Compacted regolith (variants a, b, c, d)
  - `12–13`: Basalt rock layers (a, b)
  - `14–15`: Lunar bedrock (a, b)
- **Row 2 (16–23): Dug-Out Excavated Space**
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
