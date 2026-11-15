# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Unit tests for Stage 10 polish, simulation tool, and accessibility features.

Validates:
- Headless simulation tool execution and metric tracking
- HUD smooth bar interpolation and high contrast mode
- Audio manager resilience (no-op on missing audio files)
- GameScreen controls shortcuts overlay toggle
"""

import pytest

from game.logic.clock import TickClock
from game.logic.data import load_balance
from game.logic.state import GameState
from tools.simulate import run_simulation
from game.audio import audio, AudioManager


@pytest.fixture(autouse=True)
def init_pygame():
    """Ensure pygame font and mixer subsystems are initialized for HUD tests."""
    import pygame
    pygame.font.init()
    yield


def test_simulation_tool_runs_headless():
    """Verify simulate.py runs headless for 50 ticks and returns valid results."""
    res = run_simulation(ticks=50, strategy="balanced")

    assert "outcome" in res
    assert "ticks_simulated" in res
    assert res["ticks_simulated"] <= 50
    assert "final_energy" in res
    assert "final_boredom" in res
    assert "final_revenue" in res
    assert "final_science" in res
    assert "buildings_placed" in res
    assert res["buildings_placed"] >= 1


def test_audio_manager_safe_without_files():
    """Verify audio methods safely no-op without crashes or exceptions."""
    mgr = AudioManager()
    mgr.play("non_existent_sound")
    mgr.play("click")
    mgr.play_music("music_day")
    mgr.stop_music()
    mgr.apply_settings({"audio_master": 5, "audio_music": 5, "audio_sfx": 5})
    assert mgr._master == 5


def test_hud_smooth_bar_interpolation():
    """Verify HUD interpolates display ratios toward target state values."""
    from game.ui.hud import HUD

    balance = load_balance()
    state = GameState(balance)
    clock = TickClock()
    hud = HUD(state, clock)

    initial_energy_ratio = hud.display_ratios["energy"]
    assert initial_energy_ratio == pytest.approx(0.5, rel=1e-2)

    # Dramatically drop energy in state
    state.energy = 20.0  # target ratio: 0.2
    assert state.get_indicator_info("energy")["ratio"] == pytest.approx(0.2, rel=1e-2)

    # Update HUD with dt=0.05
    hud.update(0.05)
    # The display ratio should have smoothly moved downward, between 0.2 and 0.5
    assert 0.2 < hud.display_ratios["energy"] < 0.5


def test_hud_high_contrast_toggle():
    """Verify HUD high contrast mode can be toggled."""
    from game.ui.hud import HUD

    balance = load_balance()
    state = GameState(balance)
    clock = TickClock()
    hud = HUD(state, clock)

    assert hud.high_contrast is False
    hud.high_contrast = True
    assert hud.high_contrast is True


def test_hud_bar_fill_pixels_match_theme_color():
    """Verify that each bar's fill area renders visibly in its theme.json color (Task 2)."""
    import pygame
    from game.ui.hud import HUD
    from game.logic.data import load_theme

    balance = load_balance()
    theme = load_theme()
    state = GameState(balance)
    clock = TickClock()

    # Set each indicator to ~50% so each bar has a filled area
    state.energy = 50.0
    state.science = 200.0
    state.boredom = 40.0
    state.revenue = 500.0
    state.event = 30.0

    hud = HUD(state, clock)
    # Fast-forward HUD update so display_ratios reach target ratios
    for _ in range(20):
        hud.update(0.1)

    surface = pygame.Surface((480, 24))
    surface.fill((0, 0, 0))
    hud.draw(surface, (0, 0))

    bar_colors = theme.get("bars", {})

    for key in hud.INDICATOR_KEYS:
        rect = hud.bar_rects[key]
        bar_x = rect.x + 17
        bar_y = rect.y + 5

        # Sample pixel inside the fill area (x+4, y+4)
        sample_x = bar_x + 4
        sample_y = bar_y + 4
        pixel_color = surface.get_at((sample_x, sample_y))[:3]

        expected_color = tuple(bar_colors[key])
        assert pixel_color == expected_color, (
            f"Bar '{key}' fill pixel at ({sample_x}, {sample_y}) was {pixel_color}, "
            f"expected theme color {expected_color}"
        )


def test_art_loaded_instead_of_fallbacks(tmp_path, monkeypatch):
    """Verify that when art files exist in the asset folder, game draws them instead of fallbacks (Task 3)."""
    import pygame
    from game.assets import assets
    from game.ui.widgets import Panel, Button
    from game.logic.world import BuildingInstance
    from game.ui.screens.game_screen import GameScreen
    from game.app import App

    # Redirect IMG_DIR to isolated tmp_path
    monkeypatch.setattr("game.assets.IMG_DIR", tmp_path)
    monkeypatch.setattr("game.constants.IMG_DIR", tmp_path)

    # Clear cached images and slices
    assets.images.clear()
    assets.missing.clear()
    if hasattr(assets, "_button_slices"):
        del assets._button_slices

    ui_dir = tmp_path / "ui"
    ui_dir.mkdir(parents=True)
    bld_dir = tmp_path / "buildings"
    bld_dir.mkdir(parents=True)

    # 1. Create panel.png (24x24) with unique pixel color (11, 22, 33)
    panel_img = pygame.Surface((24, 24))
    panel_img.fill((11, 22, 33))
    pygame.image.save(panel_img, str(ui_dir / "panel.png"))

    # 2. Create button.png (96x24) with unique pixel color (44, 55, 66)
    button_img = pygame.Surface((96, 24))
    button_img.fill((44, 55, 66))
    pygame.image.save(button_img, str(ui_dir / "button.png"))

    # 3. Create fuel_cell.png (32x32) with unique pixel color (77, 88, 99)
    fuel_cell_img = pygame.Surface((32, 32))
    fuel_cell_img.fill((77, 88, 99))
    pygame.image.save(fuel_cell_img, str(bld_dir / "fuel_cell.png"))

    # Verify Panel draws the custom panel art
    p = Panel(0, 0, 50, 50)
    surf_panel = pygame.Surface((50, 50))
    p.draw(surf_panel)
    # The 9-slice corners will blit the unique color (11, 22, 33)
    assert surf_panel.get_at((0, 0))[:3] == (11, 22, 33)

    # Verify Button draws the custom button art
    font = pygame.font.Font(None, 12)
    b = Button(0, 0, 40, 20, "Test", font)
    surf_btn = pygame.Surface((40, 20))
    b.draw(surf_btn)
    assert surf_btn.get_at((2, 2))[:3] == (44, 55, 66)

    # Verify building sprite draws custom fuel_cell.png
    b_inst = BuildingInstance("fuel_cell", col=10, width=2, height=2, cost=40, is_active=True)
    sprite = assets.get_building_sprite("fuel_cell", 2, 2, True, 0)
    assert sprite is not None
    assert sprite.get_at((5, 5))[:3] == (77, 88, 99)


def test_every_building_name_fits_inside_tray_card():
    """Verify every building name in buildings.json fits inside its tray card without truncation (Task 4)."""
    import pygame
    pygame.font.init()
    from game.ui.build_tray import BuildTray
    from game.logic.data import load_buildings, load_text

    tray = BuildTray()
    b_data = load_buildings()
    t_data = load_text().get("buildings", {})

    assert len(b_data) > 0

    card_rect = tray.card_rects[0]

    for b_id, b_def in b_data.items():
        if b_id == "habitat_pod":
            continue
        name = t_data.get(b_id, {}).get("name", b_id.replace("_", " ").title())
        cost = b_def.get("cost", 0)

        cost_surf = tray.font.render(f"${cost}", False, (255, 255, 255))
        # Unlocked available width: card width minus left pad (4), right pad (4), cost width, gap (2)
        avail_w_unlocked = card_rect.width - 4 - cost_surf.get_width() - 6
        # Locked available width: card width minus lock icon (20), right pad (4), cost width, gap (2)
        avail_w_locked = card_rect.width - 20 - cost_surf.get_width() - 6

        # Test unlocked name rendering
        rendered_unlocked = tray._render_card_name(name, avail_w_unlocked, card_rect.height - 4, (255, 255, 255))
        assert rendered_unlocked.get_width() <= avail_w_unlocked, (
            f"Building '{b_id}' ({name}) width {rendered_unlocked.get_width()} exceeds unlocked card space {avail_w_unlocked}"
        )
        assert rendered_unlocked.get_height() <= card_rect.height, (
            f"Building '{b_id}' ({name}) height {rendered_unlocked.get_height()} exceeds card height {card_rect.height}"
        )

        # Test locked name rendering
        rendered_locked = tray._render_card_name(name, avail_w_locked, card_rect.height - 4, (140, 140, 150))
        assert rendered_locked.get_width() <= avail_w_locked, (
            f"Building '{b_id}' ({name}) width {rendered_locked.get_width()} exceeds locked card space {avail_w_locked}"
        )
        assert rendered_locked.get_height() <= card_rect.height, (
            f"Building '{b_id}' ({name}) height {rendered_locked.get_height()} exceeds card height {card_rect.height}"
        )

    # Also test actual draw pass for all categories
    test_surf = pygame.Surface((480, 270))
    for cat in tray.categories:
        tray.active_category = cat
        tray.draw(test_surf, (100, 100), current_science=0, current_revenue=0)
        tray.draw(test_surf, (100, 100), current_science=500, current_revenue=1000)


def test_tutorial_layout_and_hint_no_overlap():
    """Verify tutorial runs with dimmed game screen and 'SPACE or ENTER' does not overlap buttons (Task 5)."""
    import pygame
    from game.ui.screens.intro_screen import IntroScreen

    class MockApp:
        def __init__(self):
            self.debug = False
            self.saved_settings = {}
            self.settings = {}

        def get_canvas_mouse_pos(self):
            return (0, 0)

        def set_screen(self, s):
            pass

    mock_app = MockApp()
    intro = IntroScreen(mock_app)

    # Test drawing on canvas
    canvas = pygame.Surface((480, 270))
    intro.draw(canvas)

    # Verify background game screen is initialized
    assert intro._bg_game_screen is not None

    # Calculate hint bounding box
    hint_txt = intro.small_font.render("SPACE or ENTER to continue", False, (255, 255, 255))
    hint_x = (10 + 140 + (480 - 90) - hint_txt.get_width()) // 2
    hint_y = 175 + 85 - 18
    hint_rect = pygame.Rect(hint_x, hint_y, hint_txt.get_width(), hint_txt.get_height())

    # Verify no overlap with Skip, Glossary, or Next buttons
    assert not hint_rect.colliderect(intro._btn_skip.rect)
    assert not hint_rect.colliderect(intro._btn_glossary.rect)
    assert not hint_rect.colliderect(intro._btn_next.rect)




