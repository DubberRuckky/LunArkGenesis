# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Top HUD bar, day/night clock, and time controls for LunArk: Genesis.

Renders the five indicator bars across the top (Energy, Science, Boredom, Revenue, Event),
lunar day/night diurnal indicator, battery life forecast, warning alerts,
hover explanations, and simulation speed controls.
"""

import pygame

from game.assets import assets, make_nine_slice
from game.constants import (
    COLOR_BAR_BG,
    COLOR_BAR_BORDER,
    COLOR_BLACK,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_NORMAL,
    COLOR_BUTTON_PRESSED,
    COLOR_ERROR,
    COLOR_REMINDER,
    COLOR_WHITE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    ICON,
    INTERNAL_WIDTH,
)
from game.logic.clock import TickClock
from game.logic.data import load_text, load_theme
from game.logic.lunar_clock import LunarClock
from game.logic.state import GameState
from game.ui.widgets import Tooltip


class HUD:
    """Top-of-screen interface managing indicators, day/night clock, and time controls."""

    INDICATOR_KEYS: list[str] = ["energy", "science", "boredom", "revenue", "event"]

    def __init__(
        self,
        state: GameState,
        clock: TickClock,
        lunar_clock: LunarClock | None = None,
    ) -> None:
        self.state = state
        self.clock = clock
        self.lunar_clock = lunar_clock

        self.theme = load_theme()
        self.text_data = load_text()

        self.font = assets.get_font(FONT_SIZE_SMALL)
        self.med_font = assets.get_font(FONT_SIZE_MEDIUM)

        # 9-slice bar frame drawer
        bar_surf = assets.load_image("bar_frame", default_size=(12, 10))
        self.draw_bar_frame = make_nine_slice(bar_surf, corner=3)

        # Smooth bar interpolation ratios (lerped towards real ratios each frame)
        self.display_ratios: dict[str, float] = {
            k: float(self.state.get_indicator_info(k)["ratio"]) for k in self.INDICATOR_KEYS
        }

        # Accessibility: High contrast mode toggle
        self.high_contrast: bool = False

        # Flash timer for warnings
        self.flash_timer: float = 0.0

        # Hook clock drop_to_1x when warning fires
        self.state.on_warning_fired = self.clock.drop_to_1x

        # Indicator bar hit rects for hover detection
        self.bar_rects: dict[str, pygame.Rect] = {}
        self._setup_rects()

        # Day/Night clock rect (x = 302, y = 2, w = 78, h = 20)
        self.lunar_rect = pygame.Rect(302, 2, 78, 20)

        # Time control button rects
        self.speed_buttons: list[dict] = [
            {"label": "||", "speed": 0, "rect": pygame.Rect(386, 4, 16, 16)},
            {"label": "1x", "speed": 1, "rect": pygame.Rect(404, 4, 16, 16)},
            {"label": "2x", "speed": 2, "rect": pygame.Rect(422, 4, 16, 16)},
            {"label": "4x", "speed": 4, "rect": pygame.Rect(440, 4, 16, 16)},
            {"label": "8x", "speed": 8, "rect": pygame.Rect(458, 4, 18, 16)},
        ]

        # Tooltip widget for hovered indicator
        self.tooltip = Tooltip(self.font)

    def _setup_rects(self) -> None:
        """Position the 5 indicator bars horizontally across the left HUD."""
        start_x = 2
        bar_spacing = 60
        for i, key in enumerate(self.INDICATOR_KEYS):
            x = start_x + i * bar_spacing
            self.bar_rects[key] = pygame.Rect(x, 2, 58, 20)

    def handle_events(self, events: list[pygame.event.Event], mouse_pos: tuple[int, int]) -> None:
        """Handle mouse clicks on time control buttons."""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.speed_buttons:
                    if btn["rect"].collidepoint(mouse_pos):
                        self.clock.set_speed(btn["speed"])
                        return

    def update(self, dt: float) -> None:
        """Update flash oscillation timer and smoothly interpolate indicator bars."""
        self.flash_timer = (self.flash_timer + dt) % 1.0
        # Lerp display ratios smoothly toward targets (speed factor = 8.0)
        for key in self.INDICATOR_KEYS:
            target = float(self.state.get_indicator_info(key)["ratio"])
            curr = self.display_ratios.get(key, target)
            self.display_ratios[key] = curr + (target - curr) * min(1.0, dt * 8.0)

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        """Render HUD background, indicator bars, day/night clock, alert banner, and time controls."""
        # 1. Background strip for HUD (480x24)
        hud_bg = pygame.Surface((INTERNAL_WIDTH, 24), pygame.SRCALPHA)
        hud_bg.fill((16, 18, 26, 235))
        surface.blit(hud_bg, (0, 0))
        pygame.draw.line(surface, (60, 65, 80), (0, 24), (INTERNAL_WIDTH, 24), 1)

        # 2. Render 5 Indicator Bars
        is_flashing = (self.flash_timer < 0.5)
        bar_colors = self.theme.get("bars", {})

        # High-contrast accessibility palette override
        high_contrast_colors = {
            "energy": (255, 235, 0),      # Saturated yellow
            "science": (0, 220, 255),     # Bright cyan
            "boredom": (220, 80, 255),    # Vibrant magenta
            "revenue": (0, 255, 120),     # Vivid neon green
            "event": (255, 50, 50),       # High-alert red
        }

        # Shape symbols for color-blind identification
        indicator_shapes = {
            "energy": "▲",
            "science": "◆",
            "boredom": "■",
            "revenue": "●",
            "event": "!",
        }

        hovered_key: str | None = None

        for key in self.INDICATOR_KEYS:
            rect = self.bar_rects[key]
            info = self.state.get_indicator_info(key)

            # Check hover
            if rect.collidepoint(mouse_pos):
                hovered_key = key

            # Progress Bar container coordinates
            bar_w = 26
            bar_h = 10
            bar_x = rect.x + 17
            bar_y = rect.y + 5
            bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)

            # Draw Order: background, fill, frame, icon, number

            # 1. Background
            pygame.draw.rect(surface, COLOR_BAR_BG, bar_rect)

            # 2. Fill (using smooth interpolated ratio)
            ratio = self.display_ratios.get(key, info["ratio"])
            fill_w = max(0, min(bar_w - 2, int((bar_w - 2) * ratio)))
            if self.high_contrast:
                color = high_contrast_colors.get(key, (220, 220, 220))
            else:
                color = tuple(bar_colors.get(key, [200, 200, 200]))

            if info["warning"] and is_flashing:
                color = COLOR_ERROR

            if fill_w > 0:
                pygame.draw.rect(surface, color, (bar_x + 1, bar_y + 1, fill_w, bar_h - 2))

            # 3. Frame
            self.draw_bar_frame(surface, bar_rect)
            if info["warning"] and is_flashing:
                pygame.draw.rect(surface, COLOR_ERROR, bar_rect, 1)

            # 4. Icon & color-blind shape badge (positioned beside/above icon, never overlapping bar)
            icon_idx = ICON.get(key, 0)
            icon_surf = assets.get_icon(icon_idx)
            surface.blit(icon_surf, (rect.x, rect.y + 2))

            shape_char = indicator_shapes.get(key, "")
            if shape_char:
                shape_surf = self.font.render(shape_char, False, (220, 225, 235))
                # Positioned at rect.x, above icon, completely outside bar_rect
                surface.blit(shape_surf, (rect.x, rect.y - 2))

            # 5. Number
            val_txt = self.font.render(str(info["value"]), False, COLOR_WHITE)
            surface.blit(val_txt, (bar_x + bar_w + 2, rect.y + 4))

        # 3. Day / Night Clock
        if self.lunar_clock:
            lc = self.lunar_clock
            # Sun (slot 14) or Moon (slot 15) icon
            icon_idx = ICON.get("sun", 14) if lc.is_day else ICON.get("moon", 15)
            phase_icon = assets.get_icon(icon_idx)
            surface.blit(phase_icon, (self.lunar_rect.x, self.lunar_rect.y + 2))

            # Small progress strip
            p_strip = pygame.Rect(self.lunar_rect.x + 18, self.lunar_rect.y + 6, 18, 8)
            pygame.draw.rect(surface, COLOR_BAR_BG, p_strip)
            ratio = lc.get_phase_ratio()
            pw = max(0, min(16, int(16 * ratio)))
            p_col = (255, 230, 80) if lc.is_day else (130, 150, 220)
            if pw > 0:
                pygame.draw.rect(surface, p_col, (p_strip.x + 1, p_strip.y + 1, pw, 6))
            pygame.draw.rect(surface, (80, 85, 100), p_strip, 1)

            # "Cycle 1/3"
            cyc_txt = self.font.render(f"C{lc.cycle}/3", False, COLOR_WHITE)
            surface.blit(cyc_txt, (self.lunar_rect.x + 39, self.lunar_rect.y + 4))

        # 4. Time control buttons
        current_speed = self.clock.get_speed()
        is_paused = self.clock.is_paused()

        for btn in self.speed_buttons:
            b_rect = btn["rect"]
            speed_val = btn["speed"]

            is_active = (is_paused and speed_val == 0) or (not is_paused and current_speed == speed_val)
            is_hover = b_rect.collidepoint(mouse_pos)

            if is_active:
                btn_color = COLOR_BUTTON_PRESSED
                border_color = (255, 220, 50)
            elif is_hover:
                btn_color = COLOR_BUTTON_HOVER
                border_color = (160, 165, 180)
            else:
                btn_color = COLOR_BUTTON_NORMAL
                border_color = (90, 95, 110)

            pygame.draw.rect(surface, btn_color, b_rect)
            pygame.draw.rect(surface, border_color, b_rect, 1)

            lbl_surf = self.font.render(btn["label"], False, COLOR_WHITE)
            lx = b_rect.x + (b_rect.width - lbl_surf.get_width()) // 2
            ly = b_rect.y + (b_rect.height - lbl_surf.get_height()) // 2
            surface.blit(lbl_surf, (lx, ly))

        # 5. Alert Banner strip (under HUD at y = 25..36)
        active_alerts: list[str] = []

        # Dusk warning 30s ahead
        if self.lunar_clock and self.lunar_clock.dusk_warning_active:
            active_alerts.append("Dusk Warning: Solar panels stop at night. Save power!")

        if self.state.warnings.get("energy"):
            active_alerts.append("Power is low! Turn off unneeded buildings.")
        if self.state.warnings.get("boredom"):
            active_alerts.append("Crew boredom is high! Build Gym or Cafe.")
        if self.state.warnings.get("revenue"):
            active_alerts.append("Revenue is low! Check datacentres and mines.")
        if self.state.warnings.get("event"):
            active_alerts.append("Hazard alert! Emergency risk is critical!")
        if self.state.event_full:
            active_alerts.append("EVENT READY: Hazard imminent!")

        if active_alerts:
            alert_msg = active_alerts[0]
            alert_w = len(alert_msg) * 7 + 24
            alert_x = (INTERNAL_WIDTH - alert_w) // 2
            alert_rect = pygame.Rect(alert_x, 26, alert_w, 13)

            bg_col = (180, 40, 40, 220) if is_flashing else (120, 30, 30, 200)
            alert_surf = pygame.Surface((alert_w, 13), pygame.SRCALPHA)
            alert_surf.fill(bg_col)
            surface.blit(alert_surf, (alert_x, 26))
            pygame.draw.rect(surface, COLOR_ERROR, alert_rect, 1)

            warn_icon = assets.get_icon(ICON.get("warning", 10))
            surface.blit(warn_icon, (alert_x + 2, 25))

            txt = self.font.render(alert_msg, False, COLOR_WHITE)
            surface.blit(txt, (alert_x + 20, 27))

        # 6. Hover Tooltip
        if hovered_key:
            info = self.state.get_indicator_info(hovered_key)
            lines = [
                f"{info['name']}: {info['value']} / {info['max']}",
                info["desc"],
                info["why"],
            ]

            # If hovering energy, include battery forecast if draining
            if hovered_key == "energy" and self.lunar_clock:
                forecast = self.lunar_clock.get_battery_forecast(info["value"], info["delta"])
                if forecast is not None:
                    lines.append(f"At this rate, battery lasts about {forecast} seconds.")

            self.tooltip.show_multiline(lines, (mouse_pos[0], 28))
            self.tooltip.draw(surface)
        else:
            self.tooltip.hide()
