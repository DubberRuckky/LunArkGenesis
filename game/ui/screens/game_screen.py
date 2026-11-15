# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Main Game screen for LunArk: Genesis.

Displays the side-view lunar landscape, HUD bars, tick clock, time controls,
camera panning, building placement ghost, build tray, lunar day/night tint,
hazard warnings, goal banner, and win/lose condition monitoring.
"""

from typing import Any
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_NORMAL,
    COLOR_BUTTON_PRESSED,
    COLOR_DARK_GREY,
    COLOR_ERROR,
    COLOR_GROUND,
    COLOR_INVALID,
    COLOR_SKY,
    COLOR_STAR,
    COLOR_VALID,
    COLOR_WHITE,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    ICON,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_LOSE,
    SCREEN_PAUSE,
    SCREEN_WIN,
    SURFACE_ROW,
    TILE_SIZE,
)
from game.logic.clock import TickClock
from game.logic.data import (
    load_balance,
    load_buildings,
    load_events,
    load_map,
    load_text,
    load_theme,
)
from game.logic.economy import calculate_building_deltas
from game.logic.events import EventManager
from game.logic.lunar_clock import LunarClock
from game.logic.objectives import ObjectiveManager
from game.logic.state import GameState
from game.logic.world import BuildingInstance, WorldGrid
from game.ui.build_tray import BuildTray
from game.ui.hud import HUD
from game.ui.screens.lose_screen import LoseScreen
from game.ui.screens.win_screen import WinScreen
from game.ui.widgets import Button, Panel


class GameScreen:
    """Core simulation screen managing world view, camera, HUD, placement, day/night, events, and objectives."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.balance = load_balance()
        self.map_data = load_map()
        self.buildings_data = load_buildings()
        self.events_data = load_events()
        self.text = load_text()
        self.theme = load_theme()

        self.clock = TickClock(tick_rate=self.balance.get("tick_rate", 1.0), initial_speed=1)
        self.lunar_clock = LunarClock(self.balance)
        self.state = GameState(self.balance)
        self.world_grid = WorldGrid(self.balance, self.map_data)
        self.event_manager = EventManager(self.events_data, self.balance)
        self.objective_manager = ObjectiveManager(self.balance, self.text)
        self.objectives = self.objective_manager
        self.hud = HUD(self.state, self.clock, self.lunar_clock)
        self.build_tray = BuildTray()

        # Store the Commander's name (passed from IntroScreen via app)
        self.player_name: str = getattr(app, "_player_name", "Commander")

        # Total play time in seconds (used by save system)
        self.play_time: float = 0.0

        # Warp drops to 1x at dusk, during events, and on critical lose countdowns
        def _on_dusk_hook() -> None:
            self.clock.drop_to_1x()
            try:
                from game.audio import audio
                audio.play("night_start")
                audio.play_music("music_night")
            except Exception:
                pass
        self.lunar_clock.on_dusk = _on_dusk_hook

        def _on_warning_hook() -> None:
            self.clock.drop_to_1x()
            try:
                from game.audio import audio
                audio.play("warning")
            except Exception:
                pass
        self.event_manager.on_warning = _on_warning_hook
        self.objective_manager.on_critical_warning = _on_warning_hook

        # Autosave at every dawn (start of a new day) and play day music
        def _autosave_dawn() -> None:
            try:
                from game.audio import audio
                audio.play_music("music_day")
            except Exception:
                pass
            from game.logic.save_load import save_game  # local import keeps logic pure
            save_game(1, self.player_name, self.play_time, self.state,
                      self.world_grid, self.lunar_clock, self.objective_manager)
        self.lunar_clock.on_dawn = _autosave_dawn

        # Stage 10 Polish & Accessibility
        self.placement_pops: list[dict[str, Any]] = []
        self.floating_texts: list[dict[str, Any]] = []
        self._last_revenue: float = self.state.revenue
        self._last_science: float = self.state.science
        self.shake_timer: float = 0.0
        self.shake_intensity: float = 0.0

        # Shortcuts overlay modal (? or / key)
        self.show_shortcuts_overlay: bool = False
        self.shortcuts_panel = Panel(80, 42, 320, 185)
        self.shortcuts_close_btn = Button(
            200, 198, 80, 18, "Close", assets.get_font(FONT_SIZE_SMALL),
            callback=self._toggle_shortcuts_overlay,
        )

        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.small_font = assets.get_font(FONT_SIZE_SMALL)
        self.title_font = assets.get_font(FONT_SIZE_LARGE)

        # World geometry
        self.world_cols = self.world_grid.world_cols
        self.tile_size = TILE_SIZE
        self.world_w_px = self.world_cols * self.tile_size  # 48 * 16 = 768 px
        self.surface_row = self.world_grid.surface_row
        self.surface_y = self.surface_row * self.tile_size  # 160 px

        # Camera
        self.camera_x: float = 0.0
        self.max_camera_x: float = float(max(0, self.world_w_px - INTERNAL_WIDTH))
        self.pan_speed: float = 240.0  # px/s
        self.pan_left: bool = False
        self.pan_right: bool = False
        self.is_dragging_cam: bool = False
        self.drag_start_x: int = 0
        self.cam_start_x: float = 0.0

        # Selected building for info panel
        self.selected_building_instance: BuildingInstance | None = None
        self.info_panel = Panel(110, 28, 260, 72)
        self.toggle_btn_rect = pygame.Rect(290, 74, 36, 16)
        self.action_btn_rect = pygame.Rect(330, 74, 36, 16)

        # First-time lunar night explanation modal
        self.night_popup_panel = Panel(100, 70, 280, 120)
        self.night_popup_btn = Button(
            195,
            160,
            90,
            18,
            "Understood",
            self.small_font,
            callback=self._dismiss_night_popup,
        )

        # Refund percent
        self.refund_percent = float(self.balance.get("economy", {}).get("demolish_refund_percent", 0.5))

        # Debug F3 indicator modifier overlay
        self.show_debug_overlay: bool = False
        self._setup_debug_overlay()

    def _dismiss_night_popup(self) -> None:
        self.lunar_clock.show_night_popup = False

    def _toggle_shortcuts_overlay(self) -> None:
        self.show_shortcuts_overlay = not self.show_shortcuts_overlay

    def _setup_debug_overlay(self) -> None:
        """Create buttons for modifying indicators in debug mode."""
        self.debug_panel = Panel(100, 40, 280, 160)
        self.debug_buttons: list[Button] = []

        keys = ["energy", "boredom", "revenue", "science", "event"]
        steps = [10, 10, 50, 50, 10]

        btn_y = 65
        for key, step in zip(keys, steps):
            b_minus = Button(
                120,
                btn_y,
                45,
                16,
                f"-{step}",
                self.small_font,
                callback=lambda k=key, s=-step: self.state.modify_indicator(k, s),
            )
            b_plus = Button(
                220,
                btn_y,
                45,
                16,
                f"+{step}",
                self.small_font,
                callback=lambda k=key, s=step: self.state.modify_indicator(k, s),
            )
            self.debug_buttons.extend([b_minus, b_plus])
            btn_y += 20

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Handle keyboard input, time controls, camera panning, and placement."""
        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]

        # Shortcuts modal intercepts input
        if self.show_shortcuts_overlay:
            self.shortcuts_close_btn.update(events, mouse_pos)
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_SLASH, pygame.K_QUESTION
                ):
                    self.show_shortcuts_overlay = False
                    return
            return

        # First-time night popup intercepts input
        if self.lunar_clock.show_night_popup:
            self.night_popup_btn.update(events, mouse_pos)
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    self._dismiss_night_popup()
                    return
            return

        # Top HUD events (y < 24)
        if mouse_pos[1] < 24:
            self.hud.handle_events(events, mouse_pos)

        # Bottom Build Tray events (y >= 220)
        tray_consumed = self.build_tray.handle_events(
            events,
            mouse_pos,
            current_science=self.state.science,
            current_revenue=self.state.revenue,
        )

        # Debug overlay clicks
        if self.show_debug_overlay and getattr(self.app, "debug", False):
            for btn in self.debug_buttons:
                btn.update(events, mouse_pos)

        for event in events:
            # Middle-mouse camera drag
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                self.is_dragging_cam = True
                self.drag_start_x = mouse_pos[0]
                self.cam_start_x = self.camera_x
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                self.is_dragging_cam = False

            elif event.type == pygame.MOUSEMOTION and self.is_dragging_cam:
                delta = self.drag_start_x - mouse_pos[0]
                self.camera_x = max(0.0, min(self.max_camera_x, self.cam_start_x + delta))

            # Left click on world (24 <= y < 220)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 24 <= mouse_pos[1] < 220 and not tray_consumed:
                    if self.selected_building_instance:
                        b = self.selected_building_instance
                        if self.toggle_btn_rect.collidepoint(mouse_pos):
                            b.is_active = not b.is_active
                            return
                        elif self.action_btn_rect.collidepoint(mouse_pos):
                            if b.is_broken:
                                self.event_manager.repair_building(b, self.state)
                            elif b.building_id == "solar_array" and b.dust_level > 0:
                                self.event_manager.clean_solar_array(b, self.state)
                            elif not b.is_shielded:
                                self.event_manager.shield_building(b, self.state)
                            return

                    world_x = mouse_pos[0] + int(self.camera_x)
                    snapped_col = world_x // self.tile_size

                    # Case A: Building Placement
                    if self.build_tray.selected_building:
                        b_def = self.build_tray.selected_building
                        success, inst, new_rev, reason = self.world_grid.place_building(
                            building_id=b_def["id"],
                            col=snapped_col,
                            width=b_def["width"],
                            height=b_def["height"],
                            cost=b_def["cost"],
                            current_revenue=self.state.revenue,
                        )
                        if success:
                            self.state.revenue = new_rev
                            self.build_tray.cancel_selection()
                            self.selected_building_instance = inst
                            try:
                                from game.audio import audio
                                audio.play("build")
                            except Exception:
                                pass
                            self.placement_pops.append({
                                "col": snapped_col,
                                "width": b_def["width"],
                                "height": b_def["height"],
                                "time": 0.0,
                                "duration": 0.4,
                            })
                        else:
                            try:
                                from game.audio import audio
                                audio.play("error")
                            except Exception:
                                pass

                    # Case B: Demolish Tool
                    elif self.build_tray.demolish_mode:
                        success, inst, new_rev, msg = self.world_grid.demolish_building(
                            col=snapped_col,
                            refund_percent=self.refund_percent,
                            current_revenue=self.state.revenue,
                        )
                        if success:
                            self.state.revenue = new_rev
                            if self.selected_building_instance == inst:
                                self.selected_building_instance = None
                            try:
                                from game.audio import audio
                                audio.play("click")
                            except Exception:
                                pass

                    # Case C: Select building for info panel
                    else:
                        inst = self.world_grid.get_building_at(snapped_col)
                        self.selected_building_instance = inst

            # Right click cancels placement/demolish/selection
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.build_tray.cancel_selection()
                self.selected_building_instance = None

            # Keyboard controls
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.pan_left = True
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.pan_right = True

                elif event.key == pygame.K_ESCAPE:
                    if self.show_debug_overlay:
                        self.show_debug_overlay = False
                        return
                    if self.build_tray.selected_building or self.build_tray.demolish_mode:
                        self.build_tray.cancel_selection()
                        return
                    if self.selected_building_instance:
                        self.selected_building_instance = None
                        return
                    if hasattr(self.app, "push_screen"):
                        self.app.push_screen(SCREEN_PAUSE)  # type: ignore[attr-defined]

                # Space: Pause
                elif event.key == pygame.K_SPACE:
                    self.clock.toggle_pause()

                # H: show tutorial glossary overlay (help)
                elif event.key == pygame.K_h:
                    if hasattr(self.app, "set_screen"):
                        self.app.push_screen("intro")  # type: ignore[attr-defined]

                # ? or /: toggle keyboard shortcuts overlay
                elif event.key in (pygame.K_SLASH, pygame.K_QUESTION):
                    self._toggle_shortcuts_overlay()

                # C: toggle high contrast HUD mode
                elif event.key == pygame.K_c:
                    self.hud.high_contrast = not self.hud.high_contrast

                # Speeds 1-4
                elif event.key == pygame.K_1:
                    self.clock.set_speed(1)
                elif event.key == pygame.K_2:
                    self.clock.set_speed(2)
                elif event.key == pygame.K_3:
                    self.clock.set_speed(4)
                elif event.key == pygame.K_4:
                    self.clock.set_speed(8)

                # Debug shortcuts
                if getattr(self.app, "debug", False):
                    if event.key == pygame.K_F3:
                        self.show_debug_overlay = not self.show_debug_overlay
                    elif event.key == pygame.K_F4:
                        self._trigger_win()
                    elif event.key == pygame.K_F5:
                        self._trigger_lose("energy")

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.pan_left = False
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.pan_right = False

    def _trigger_win(self) -> None:
        """Trigger victory screen transition with stats."""
        stats = {
            "cycles": self.lunar_clock.cycle,
            "buildings": len(self.world_grid.buildings),
            "science": int(self.state.science),
        }
        hint = self.objective_manager.get_win_hint()
        if hasattr(self.app, "set_screen_instance"):
            self.app.set_screen_instance(WinScreen(self.app, stats=stats, hint=hint))
        elif hasattr(self.app, "set_screen"):
            self.app.set_screen(SCREEN_WIN)

    def _trigger_lose(self, cause: str) -> None:
        """Trigger defeat screen transition with stats and hint."""
        stats = {
            "cycles": self.lunar_clock.cycle,
            "buildings": len(self.world_grid.buildings),
            "science": int(self.state.science),
        }
        hint = self.objective_manager.get_lose_hint(cause)
        if hasattr(self.app, "set_screen_instance"):
            self.app.set_screen_instance(LoseScreen(self.app, cause=cause, stats=stats, hint=hint))
        elif hasattr(self.app, "set_screen"):
            self.app.set_screen(SCREEN_LOSE)

    def update(self, dt: float) -> None:
        """Advance camera, simulation ticks with building economy, day/night, events, and goals."""
        # Accumulate real time for the save system
        self.play_time += dt

        # Camera panning
        if self.pan_left:
            self.camera_x = max(0.0, self.camera_x - self.pan_speed * dt)
        if self.pan_right:
            self.camera_x = min(self.max_camera_x, self.camera_x + self.pan_speed * dt)

        # Simulation ticks with economy, diurnal, event, and goal evaluation
        ticks_elapsed = self.clock.update(dt)
        for _ in range(ticks_elapsed):
            self.lunar_clock.tick()
            is_day = self.lunar_clock.is_day
            solar_eff = self.lunar_clock.get_solar_efficiency()
            heating = self.lunar_clock.get_heating_load()

            b_deltas = calculate_building_deltas(
                self.world_grid.buildings,
                self.buildings_data,
                is_day=is_day,
                solar_efficiency=solar_eff,
                heating_load=heating,
            )
            self.state.tick(cycle=self.lunar_clock.cycle, external_deltas=b_deltas)

            # Advance events
            self.event_manager.tick(
                event_bar_full=self.state.event_full,
                buildings=self.world_grid.buildings,
                state=self.state,
            )

            # Advance win/lose objectives
            obj_status = self.objective_manager.tick(
                self.world_grid.buildings,
                self.state,
                self.lunar_clock,
            )

            if obj_status["is_won"]:
                self._trigger_win()
                return
            elif obj_status["is_lost"]:
                self._trigger_lose(obj_status["lose_cause"] or "energy")
                return

        # Stage 10: Check income delta for floating +$N and +N Sci
        rev_gain = self.state.revenue - self._last_revenue
        if rev_gain >= 1.0:
            self.floating_texts.append({
                "x": 190,
                "y": 28,
                "text": f"+${int(rev_gain)}",
                "color": (120, 255, 140),
                "time": 0.0,
                "duration": 1.2,
            })
        self._last_revenue = self.state.revenue

        sci_gain = self.state.science - self._last_science
        if sci_gain >= 1.0:
            self.floating_texts.append({
                "x": 75,
                "y": 28,
                "text": f"+{int(sci_gain)} Sci",
                "color": (100, 220, 255),
                "time": 0.0,
                "duration": 1.2,
            })
        self._last_science = self.state.science

        # Screen shake trigger on meteor event impact
        if self.event_manager.active_event and self.event_manager.active_event.get("id") == "micrometeorite":
            if self.event_manager.countdown <= 1.0 and self.shake_timer <= 0.0:
                self.shake_timer = 0.4
                self.shake_intensity = 3.5

        if self.shake_timer > 0.0:
            self.shake_timer = max(0.0, self.shake_timer - dt)

        # Update placement pop animations
        for pop in self.placement_pops:
            pop["time"] += dt
        self.placement_pops = [p for p in self.placement_pops if p["time"] < p["duration"]]

        # Update floating text
        for ft in self.floating_texts:
            ft["time"] += dt
            ft["y"] -= 12.0 * dt
        self.floating_texts = [f for f in self.floating_texts if f["time"] < f["duration"]]

        self.hud.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Render sky, terrain, buildings, night tint, ghost, events, goal banner, HUD, and info panels."""
        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]

        # Screen shake offset
        shake_x = 0
        shake_y = 0
        if self.shake_timer > 0.0:
            import random
            shake_x = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            shake_y = random.randint(-int(self.shake_intensity), int(self.shake_intensity))

        cam_x = int(self.camera_x) + shake_x
        surface_y = self.surface_y + shake_y

        # 1. Sky & Stars
        if "stars" not in assets.missing:
            surface.blit(assets.load_image("stars"), (0, 0))
        else:
            surface.fill(COLOR_SKY)
            for sx, sy in [(30, 40), (110, 70), (220, 50), (330, 80), (440, 35)]:
                surface.set_at((sx, sy), COLOR_STAR)

        # Parallax Far Horizon (0.3x parallax)
        far_x = -int(cam_x * 0.3) % INTERNAL_WIDTH
        if "horizon_far" not in assets.missing:
            surf_far = assets.load_image("horizon_far")
            surface.blit(surf_far, (far_x, self.surface_y - 90))
            if far_x > 0:
                surface.blit(surf_far, (far_x - INTERNAL_WIDTH, self.surface_y - 90))
            elif far_x + surf_far.get_width() < INTERNAL_WIDTH:
                surface.blit(surf_far, (far_x + surf_far.get_width(), self.surface_y - 90))

        # Parallax Near Horizon (0.6x parallax)
        near_x = -int(cam_x * 0.6) % INTERNAL_WIDTH
        if "horizon_near" not in assets.missing:
            surf_near = assets.load_image("horizon_near")
            surface.blit(surf_near, (near_x, self.surface_y - 60))
            if near_x > 0:
                surface.blit(surf_near, (near_x - INTERNAL_WIDTH, self.surface_y - 60))
            elif near_x + surf_near.get_width() < INTERNAL_WIDTH:
                surface.blit(surf_near, (near_x + surf_near.get_width(), self.surface_y - 60))

        # 2. Lunar Terrain
        tile_map = self.map_data.get("tile_layout", {})
        for col in range(self.world_cols):
            tx = col * self.tile_size - cam_x
            if -self.tile_size <= tx <= INTERNAL_WIDTH:
                tile_idx = int(tile_map.get(str(col), 0))
                tile_surf = assets.get_tile(tile_idx)
                surface.blit(tile_surf, (tx, surface_y))

                ug_rect = pygame.Rect(tx, surface_y + self.tile_size, self.tile_size, INTERNAL_HEIGHT - (surface_y + self.tile_size))
                pygame.draw.rect(surface, (70, 70, 68), ug_rect)

        # 3. Placed Buildings
        for b in self.world_grid.buildings:
            bx = b.col * self.tile_size - cam_x
            by = surface_y - b.height * self.tile_size
            bw = b.width * self.tile_size
            bh = b.height * self.tile_size

            if -bw <= bx <= INTERNAL_WIDTH:
                self._draw_building(surface, b, bx, by, bw, bh)

        # 3b. Placement Pop Animations
        for pop in self.placement_pops:
            t = pop["time"] / pop["duration"]
            col = pop["col"]
            px = col * self.tile_size - cam_x
            py = surface_y - pop["height"] * self.tile_size
            pw = pop["width"] * self.tile_size
            ph = pop["height"] * self.tile_size

            expand = int((1.0 - t) * 6)
            rect = pygame.Rect(px - expand, py - expand, pw + expand * 2, ph + expand * 2)
            pop_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            alpha = int((1.0 - t) * 200)
            pygame.draw.rect(pop_surf, (150, 255, 255, alpha), pop_surf.get_rect(), max(1, int(2 * (1.0 - t))))
            surface.blit(pop_surf, rect.topleft)

        # 4. Smooth Night Tint
        night_alpha_factor = self.lunar_clock.get_night_tint_alpha()
        if night_alpha_factor > 0.01:
            tint_cfg = self.theme.get("night_tint", [15, 20, 50, 160])
            target_alpha = int(tint_cfg[3] * night_alpha_factor)
            tint_surf = pygame.Surface((INTERNAL_WIDTH, 196), pygame.SRCALPHA)
            tint_surf.fill((tint_cfg[0], tint_cfg[1], tint_cfg[2], target_alpha))
            surface.blit(tint_surf, (0, 24))

        # 5. Goal Banner under HUD (y = 25..36) or Critical Alert
        crit_msg = self.objective_manager.critical_alert
        if crit_msg:
            # Flashing red countdown alert
            crit_surf = pygame.Surface((INTERNAL_WIDTH, 14), pygame.SRCALPHA)
            crit_surf.fill((200, 30, 30, 230))
            surface.blit(crit_surf, (0, 25))
            pygame.draw.line(surface, COLOR_ERROR, (0, 38), (INTERNAL_WIDTH, 38), 1)

            w_icon = assets.get_icon(ICON.get("warning", 10))
            surface.blit(w_icon, (6, 24))

            c_txt = self.small_font.render(crit_msg, False, COLOR_WHITE)
            surface.blit(c_txt, (26, 26))

        elif self.event_manager.active_event:
            # Event countdown banner with optional event illustration
            ev = self.event_manager.active_event
            cd = self.event_manager.countdown
            banner_y = 25

            ev_id = ev.get("id", "")
            ev_img = assets.get_event_image(ev_id)
            ev_name = ev.get("name", "Hazard")
            banner_txt = f"{ev_name.upper()} IN {cd}s! {ev.get('text', '')}"

            from game.ui.widgets import build_text_box
            banner_box = build_text_box(
                banner_txt,
                self.small_font,
                max_width=340,
                bg_color=(160, 30, 30, 225),
                padding=3,
            )
            banner_w = banner_box.get_width()
            banner_x = (INTERNAL_WIDTH - banner_w) // 2
            surface.blit(banner_box, (banner_x, banner_y))

            if ev_img:
                surface.blit(ev_img, (banner_x - ev_img.get_width() - 4, banner_y - 20))
            else:
                w_icon = assets.get_icon(ICON.get("warning", 10))
                surface.blit(w_icon, (banner_x + 3, banner_y + 1))

        else:
            # Standard Goal Banner
            goal_txt = self.objective_manager.get_goal_banner_text(self.lunar_clock.cycle)
            g_surf = self.small_font.render(goal_txt, False, (160, 220, 255))
            surface.blit(g_surf, ((INTERNAL_WIDTH - g_surf.get_width()) // 2, 26))

            # Checkmark if research is complete
            if self.objective_manager.is_research_complete:
                chk = assets.get_icon(ICON.get("check", 21))
                surface.blit(chk, ((INTERNAL_WIDTH + g_surf.get_width()) // 2 + 4, 25))

        # 6. Placement Ghost or Demolish Highlight
        world_x = mouse_pos[0] + cam_x
        snapped_col = world_x // self.tile_size

        if self.build_tray.selected_building and (24 <= mouse_pos[1] < 220):
            b_def = self.build_tray.selected_building
            w = b_def["width"]
            h = b_def["height"]
            cost = b_def["cost"]
            valid, reason = self.world_grid.can_place(snapped_col, w, cost, self.state.revenue)

            gx = snapped_col * self.tile_size - cam_x
            gy = self.surface_y - h * self.tile_size
            gw = w * self.tile_size
            gh = h * self.tile_size

            ghost_surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
            fill_color = (80, 220, 80, 120) if valid else (220, 60, 60, 120)
            border_color = COLOR_VALID if valid else COLOR_INVALID
            ghost_surf.fill(fill_color)
            surface.blit(ghost_surf, (gx, gy))
            pygame.draw.rect(surface, border_color, pygame.Rect(gx, gy, gw, gh), 1)

            lbl = self.small_font.render(b_def["name"], False, COLOR_WHITE)
            surface.blit(lbl, (gx + 2, gy + 2))

            hint_txt = f"${cost}" if valid else reason
            hint_col = (80, 220, 80) if valid else (240, 70, 70)
            hint_surf = self.small_font.render(hint_txt, False, hint_col)
            surface.blit(hint_surf, (gx, gy - 12))

        elif self.build_tray.demolish_mode and (24 <= mouse_pos[1] < 220):
            target_b = self.world_grid.get_building_at(snapped_col)
            if target_b:
                dx = target_b.col * self.tile_size - cam_x
                dy = self.surface_y - target_b.height * self.tile_size
                dw = target_b.width * self.tile_size
                dh = target_b.height * self.tile_size

                highlight = pygame.Surface((dw, dh), pygame.SRCALPHA)
                highlight.fill((220, 40, 40, 100))
                surface.blit(highlight, (dx, dy))
                pygame.draw.rect(surface, COLOR_ERROR, pygame.Rect(dx, dy, dw, dh), 1)

                refund = int(target_b.cost * self.refund_percent)
                txt = self.small_font.render(f"Demolish: +${refund}", False, (255, 100, 100))
                surface.blit(txt, (dx, dy - 12))

        # 7. Building Info Panel
        hovered_b = self.world_grid.get_building_at(snapped_col) if (24 <= mouse_pos[1] < 220 and not self.build_tray.selected_building and not self.build_tray.demolish_mode) else None
        active_info_b = self.selected_building_instance or hovered_b

        if active_info_b and not self.build_tray.selected_building and not self.build_tray.demolish_mode:
            self._draw_info_panel(surface, active_info_b, mouse_pos)

        # 8. Bottom Build Tray
        self.build_tray.draw(
            surface,
            mouse_pos,
            current_science=self.state.science,
            current_revenue=self.state.revenue,
        )

        # 9. Top HUD
        self.hud.draw(surface, mouse_pos)

        # 9b. Floating Resource Gain Texts (+$$$ and +Sci)
        for ft in self.floating_texts:
            t = ft["time"] / ft["duration"]
            alpha = max(0, min(255, int((1.0 - t) * 255)))
            txt_surf = self.small_font.render(ft["text"], False, ft["color"])
            txt_surf.set_alpha(alpha)
            surface.blit(txt_surf, (int(ft["x"]), int(ft["y"])))

        # 10. First-time Lunar Night Modal Explanation
        if self.lunar_clock.show_night_popup:
            self._draw_night_popup(surface)

        # 11. Shortcuts Overlay (? key)
        if self.show_shortcuts_overlay:
            self._draw_shortcuts_overlay(surface)

        # 12. Debug indicator overlay
        if self.show_debug_overlay and getattr(self.app, "debug", False):
            self._draw_debug_overlay(surface)

    def _draw_shortcuts_overlay(self, surface: pygame.Surface) -> None:
        """Draw interactive keyboard shortcuts and controls guide."""
        dim_surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 160))
        surface.blit(dim_surf, (0, 0))

        self.shortcuts_panel.draw(surface)
        px = self.shortcuts_panel.rect.x
        py = self.shortcuts_panel.rect.y

        t_surf = self.font.render("Keyboard Controls Guide", False, (255, 220, 80))
        surface.blit(t_surf, (px + 14, py + 8))

        shortcuts = [
            ("Space", "Pause or resume simulation time"),
            ("1 / 2 / 3 / 4", "Set speed (1x, 2x, 4x, 8x)"),
            ("A / D / Arrows", "Pan camera across Moon base"),
            ("Middle Mouse Drag", "Pan camera smoothly"),
            ("Left Click", "Select card / Place building"),
            ("Right Click / Esc", "Cancel placement / Open menu"),
            ("H", "Lieutenant dialogue & glossary"),
            ("C", "Toggle high contrast HUD"),
            ("F11", "Toggle fullscreen display"),
            ("? or /", "Close this guide"),
        ]
        y_pos = py + 26
        for key_label, desc in shortcuts:
            k_txt = self.small_font.render(key_label, False, (140, 200, 255))
            d_txt = self.small_font.render(desc, False, COLOR_WHITE)
            surface.blit(k_txt, (px + 14, y_pos))
            surface.blit(d_txt, (px + 120, y_pos))
            y_pos += 12

        self.shortcuts_close_btn.draw(surface)

    def _draw_night_popup(self, surface: pygame.Surface) -> None:
        """Draw first-time modal dialog explaining the 180s lunar night."""
        dim_surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 140))
        surface.blit(dim_surf, (0, 0))

        self.night_popup_panel.draw(surface)
        px = self.night_popup_panel.rect.x
        py = self.night_popup_panel.rect.y

        t_surf = self.title_font.render("Lunar Night Arrives!", False, (80, 180, 255))
        surface.blit(t_surf, (px + 12, py + 10))

        lines = [
            "The Moon is in total darkness for 180 seconds.",
            "Solar arrays stop producing power completely.",
            "Base heating draws an extra 3 Energy every second.",
            "Use Fuel Cells to keep power running until dawn!",
        ]
        y_offset = py + 36
        for line in lines:
            l_surf = self.small_font.render(line, False, COLOR_WHITE)
            surface.blit(l_surf, (px + 12, y_offset))
            y_offset += 14

        self.night_popup_btn.draw(surface)

    def _draw_building(
        self,
        surface: pygame.Surface,
        b: BuildingInstance,
        bx: int,
        by: int,
        bw: int,
        bh: int,
    ) -> None:
        """Draw building sprite, regolith shielding, dust overlay, or broken sparks."""
        anim_tick = int(getattr(self.clock, "total_ticks", 0))
        b_sprite = assets.get_building_sprite(
            b.building_id,
            b.width,
            b.height,
            b.is_active and not b.is_broken,
            anim_tick,
        )
        if b_sprite is not None:
            b_surf = b_sprite.copy()
        else:
            b_surf = pygame.Surface((bw, bh))
            if not b.is_active or b.is_broken:
                b_surf.fill((40, 40, 45))
                border_c = (90, 90, 100) if not b.is_broken else COLOR_ERROR
                pygame.draw.rect(b_surf, border_c, b_surf.get_rect(), 1)
            elif b.building_id == "habitat_pod":
                b_surf.fill((50, 70, 95))
                pygame.draw.rect(b_surf, (100, 140, 190), b_surf.get_rect(), 1)
            elif "generator" in b.building_id or "fuel" in b.building_id or "solar" in b.building_id or "nuclear" in b.building_id:
                b_surf.fill((80, 75, 45))
                pygame.draw.rect(b_surf, (220, 200, 60), b_surf.get_rect(), 1)
            elif "data" in b.building_id or "metal" in b.building_id or "helium" in b.building_id:
                b_surf.fill((45, 75, 50))
                pygame.draw.rect(b_surf, (80, 220, 80), b_surf.get_rect(), 1)
            elif "gym" in b.building_id or "cafe" in b.building_id or "restaurant" in b.building_id:
                b_surf.fill((75, 45, 75))
                pygame.draw.rect(b_surf, (200, 80, 200), b_surf.get_rect(), 1)
            else:
                b_surf.fill((45, 65, 85))
                pygame.draw.rect(b_surf, (80, 180, 255), b_surf.get_rect(), 1)

        # Status icon in corner
        if not b.is_active:
            off_icon = assets.get_icon(ICON.get("offline", 11))
            b_surf.blit(off_icon, (bw - 17, bh - 17))
        elif b.is_broken:
            spark_fx = assets.get_fx("sparks", 16, 16, anim_tick)
            if spark_fx:
                b_surf.blit(spark_fx, (bw // 2 - 8, bh // 2 - 8))
            broken_icon = assets.get_icon(ICON.get("broken", 12))
            b_surf.blit(broken_icon, (bw - 17, bh - 17))

        # Shielding indicator
        if b.is_shielded:
            shield_icon = assets.get_icon(ICON.get("radiation", 22))
            b_surf.blit(shield_icon, (2, bh - 17))

        # Dust overlay on solar panels
        if b.dust_level > 0:
            dust_fx = assets.get_fx("dust_puff", 16, 16, anim_tick)
            if dust_fx:
                b_surf.blit(dust_fx, (0, 0))
            else:
                dust_col = (140, 130, 110, 120 if b.dust_level == 1 else 190)
                d_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                d_surf.fill(dust_col)
                b_surf.blit(d_surf, (0, 0))

        surface.blit(b_surf, (bx, by))

        # Regolith mound over top of shielded building
        if b.is_shielded:
            mound_rect = pygame.Rect(bx, by - 4, bw, 4)
            pygame.draw.rect(surface, (130, 130, 125), mound_rect)

        if self.selected_building_instance == b:
            pygame.draw.rect(surface, (255, 240, 80), pygame.Rect(bx, by, bw, bh), 1)

    def _draw_info_panel(
        self,
        surface: pygame.Surface,
        b: BuildingInstance,
        mouse_pos: tuple[int, int],
    ) -> None:
        """Render info panel for a placed building with on/off and action buttons."""
        px = 110
        py = 28
        self.info_panel.rect.x = px
        self.info_panel.rect.y = py
        self.info_panel.draw(surface)

        b_def = self.buildings_data.get(b.building_id, {})
        txt_info = self.text.get("buildings", {}).get(b.building_id, {})
        name = txt_info.get("name", b.building_id.replace("_", " ").title())
        desc = txt_info.get("desc", "Base module.")

        t_surf = self.small_font.render(f"{name} ({b.width}x{b.height})", False, (80, 180, 255))
        surface.blit(t_surf, (px + 6, py + 5))

        from game.ui.widgets import wrap_text_to_width
        desc_lines = wrap_text_to_width(desc, self.small_font, max_width=248)
        if desc_lines:
            d_surf = self.small_font.render(desc_lines[0], False, COLOR_WHITE)
            surface.blit(d_surf, (px + 6, py + 19))

        e_rate = b_def.get("energy_rate", 0)
        r_rate = b_def.get("revenue_rate", 0)
        s_rate = b_def.get("science_rate", 0)
        b_rate = b_def.get("boredom_rate", 0)

        stats_parts: list[str] = []
        if e_rate != 0:
            if b.building_id == "solar_array" and not self.lunar_clock.is_day:
                stats_parts.append("Power: 0 (Night)")
            else:
                stats_parts.append(f"Power: {'+' if e_rate > 0 else ''}{e_rate}")
        if r_rate != 0:
            stats_parts.append(f"Rev: +{r_rate}")
        if s_rate != 0:
            stats_parts.append(f"Sci: +{s_rate}")
        if b_rate != 0:
            stats_parts.append(f"Boredom: {b_rate}")

        stats_line = " | ".join(stats_parts) if stats_parts else "Passive Life Support"
        st_surf = self.small_font.render(stats_line, False, (180, 220, 180))
        surface.blit(st_surf, (px + 6, py + 34))

        # Status readout
        shield_txt = " [Shielded]" if b.is_shielded else ""
        dust_txt = f" [Dust L{b.dust_level}]" if b.dust_level > 0 else ""
        broken_txt = " [BROKEN]" if b.is_broken else ""
        cond_surf = self.small_font.render(f"Cond:{shield_txt}{dust_txt}{broken_txt}", False, (255, 200, 100))
        surface.blit(cond_surf, (px + 6, py + 52))

        # Button 1: Power ON/OFF Toggle
        btn_x = px + 165
        btn_y = py + 50
        self.toggle_btn_rect.x = btn_x
        self.toggle_btn_rect.y = btn_y
        self.toggle_btn_rect.width = 40
        self.toggle_btn_rect.height = 16

        is_hover = self.toggle_btn_rect.collidepoint(mouse_pos)
        if b.is_active:
            btn_bg = (50, 140, 60) if not is_hover else (70, 170, 80)
            btn_lbl = "ON"
        else:
            btn_bg = (120, 40, 40) if not is_hover else (150, 50, 50)
            btn_lbl = "OFF"

        pygame.draw.rect(surface, btn_bg, self.toggle_btn_rect)
        pygame.draw.rect(surface, COLOR_WHITE, self.toggle_btn_rect, 1)

        lbl_surf = self.small_font.render(btn_lbl, False, COLOR_WHITE)
        lx = btn_x + (self.toggle_btn_rect.width - lbl_surf.get_width()) // 2
        ly = btn_y + (self.toggle_btn_rect.height - lbl_surf.get_height()) // 2
        surface.blit(lbl_surf, (lx, ly))

        # Button 2: Action Button (Shield / Clean / Repair)
        act_x = px + 210
        act_y = py + 50
        self.action_btn_rect.x = act_x
        self.action_btn_rect.y = act_y
        self.action_btn_rect.width = 44
        self.action_btn_rect.height = 16

        act_hover = self.action_btn_rect.collidepoint(mouse_pos)
        if b.is_broken:
            act_lbl = "Fix $25"
            act_bg = (180, 50, 50) if not act_hover else (210, 70, 70)
        elif b.building_id == "solar_array" and b.dust_level > 0:
            act_lbl = "Cln $15"
            act_bg = (160, 140, 50) if not act_hover else (190, 170, 70)
        elif not b.is_shielded:
            act_lbl = "Shld$30"
            act_bg = (60, 90, 140) if not act_hover else (80, 110, 170)
        else:
            act_lbl = "Safe"
            act_bg = (40, 50, 65)

        pygame.draw.rect(surface, act_bg, self.action_btn_rect)
        pygame.draw.rect(surface, (180, 185, 200), self.action_btn_rect, 1)

        albl_surf = self.small_font.render(act_lbl, False, COLOR_WHITE)
        ax = act_x + (self.action_btn_rect.width - albl_surf.get_width()) // 2
        ay = act_y + (self.action_btn_rect.height - albl_surf.get_height()) // 2
        surface.blit(albl_surf, (ax, ay))

    def _draw_debug_overlay(self, surface: pygame.Surface) -> None:
        """Draw the indicator tuning debug panel."""
        self.debug_panel.draw(surface)
        title = self.small_font.render("DEBUG: Modify Indicators (F3)", False, (80, 180, 255))
        surface.blit(title, (self.debug_panel.rect.x + 10, self.debug_panel.rect.y + 8))

        keys = ["energy", "boredom", "revenue", "science", "event"]
        btn_y = self.debug_panel.rect.y + 25
        for key in keys:
            val = int(getattr(self.state, key, 0))
            lbl = self.small_font.render(f"{key.capitalize():8}: {val:4}", False, COLOR_WHITE)
            surface.blit(lbl, (self.debug_panel.rect.x + 10, btn_y + 2))
            btn_y += 20

        for btn in self.debug_buttons:
            btn.draw(surface)
