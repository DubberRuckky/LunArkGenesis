# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Build tray and category selector UI for LunArk: Genesis.

Sits at the bottom of the screen (50px tall).
Provides 4 category tabs (Generator, Cashflow, Activity, Science),
three building tier cards per category, lock state indicators, and a Demolish tool.
"""

from typing import Any
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_NORMAL,
    COLOR_BUTTON_PRESSED,
    COLOR_ERROR,
    COLOR_WHITE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    ICON,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
)
from game.logic.data import load_buildings, load_text
from game.logic.economy import is_building_unlocked


class BuildTray:
    """Bottom tray interface for selecting buildings to construct or demolish."""

    def __init__(self) -> None:
        self.font = assets.get_font(FONT_SIZE_SMALL)
        self.med_font = assets.get_font(FONT_SIZE_MEDIUM)

        self.categories = ["generator", "cashflow", "activity", "science"]
        self.active_category: str = "generator"

        # Load definitions from JSON
        self.catalogue = load_buildings()
        self.text_data = load_text().get("buildings", {})

        # Active tool state: None, a building dict, or "demolish"
        self.selected_building: dict[str, Any] | None = None
        self.demolish_mode: bool = False
        self.lock_message: str | None = None

        # Tray coordinates: 50px tall at bottom
        self.tray_rect = pygame.Rect(0, INTERNAL_HEIGHT - 50, INTERNAL_WIDTH, 50)
        from game.assets import make_nine_slice
        panel_surf = assets.load_image("panel", default_size=(24, 24))
        self.nine_slice = make_nine_slice(panel_surf, corner=8)

        # Tab button rects
        self.tab_rects: dict[str, pygame.Rect] = {
            "generator": pygame.Rect(4, INTERNAL_HEIGHT - 47, 44, 18),
            "cashflow": pygame.Rect(50, INTERNAL_HEIGHT - 47, 44, 18),
            "activity": pygame.Rect(96, INTERNAL_HEIGHT - 47, 44, 18),
            "science": pygame.Rect(142, INTERNAL_HEIGHT - 47, 44, 18),
        }

        # Demolish button rect
        self.demolish_rect = pygame.Rect(INTERNAL_WIDTH - 64, INTERNAL_HEIGHT - 47, 60, 18)

        # 3 tier card rects in the tray
        self.card_rects: list[pygame.Rect] = [
            pygame.Rect(4, INTERNAL_HEIGHT - 25, 154, 22),
            pygame.Rect(162, INTERNAL_HEIGHT - 25, 154, 22),
            pygame.Rect(320, INTERNAL_HEIGHT - 25, 154, 22),
        ]

    def _render_card_name(
        self,
        name: str,
        max_w: int,
        max_h: int,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        """Render card name fitting within max_w and max_h using appropriate font size or wrapping."""
        # 1. Try standard font if it fits
        w, h = self.font.size(name)
        if w <= max_w:
            return self.font.render(name, False, color)

        # 2. Try smaller font sizes (10, 9, 8)
        for sz in (10, 9, 8):
            f = assets.get_font(sz)
            if f.size(name)[0] <= max_w:
                return f.render(name, False, color)

        # 3. If still exceeds, wrap text to fit max_w using small font
        f = assets.get_font(8)
        from game.ui.widgets import wrap_text_to_width
        lines = wrap_text_to_width(name, f, max_w)
        surf = pygame.Surface((max_w, max_h), pygame.SRCALPHA)
        line_h = f.get_linesize()
        for idx, line in enumerate(lines[:2]):
            line_surf = f.render(line, False, color)
            surf.blit(line_surf, (0, idx * line_h))
        return surf

    def get_category_cards(self, category: str) -> list[dict[str, Any]]:
        """Fetch list of 3 building definitions for the given category from JSON catalogue."""
        cards: list[dict[str, Any]] = []
        for b_id, b_data in self.catalogue.items():
            if b_data.get("category") == category and b_id != "habitat_pod":
                fp = b_data.get("footprint", [2, 2])
                name = self.text_data.get(b_id, {}).get("name", b_id.replace("_", " ").title())
                cards.append({
                    "id": b_id,
                    "name": name,
                    "tier": b_data.get("tier", 1),
                    "width": fp[0],
                    "height": fp[1],
                    "cost": b_data.get("cost", 50),
                    "energy_rate": b_data.get("energy_rate", 0),
                    "revenue_rate": b_data.get("revenue_rate", 0),
                    "science_rate": b_data.get("science_rate", 0),
                    "boredom_rate": b_data.get("boredom_rate", 0),
                    "unlock_req": b_data.get("unlock_req", {"science": 0, "revenue": 0}),
                })
        cards.sort(key=lambda x: x["tier"])
        return cards

    def cancel_selection(self) -> None:
        """Clear active building placement ghost and demolish tool."""
        self.selected_building = None
        self.demolish_mode = False
        self.lock_message = None

    def handle_events(
        self,
        events: list[pygame.event.Event],
        mouse_pos: tuple[int, int],
        current_science: float = 0.0,
        current_revenue: float = 0.0,
    ) -> bool:
        """Handle clicks on tabs, building cards, or demolish tool."""
        for event in events:
            # Right-click cancels placement
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.cancel_selection()
                return True

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.selected_building or self.demolish_mode:
                    self.cancel_selection()
                    return True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 1. Check Demolish tool
                if self.demolish_rect.collidepoint(mouse_pos):
                    self.demolish_mode = not self.demolish_mode
                    self.selected_building = None
                    self.lock_message = None
                    return True

                # 2. Check category tabs
                for cat, r in self.tab_rects.items():
                    if r.collidepoint(mouse_pos):
                        self.active_category = cat
                        self.demolish_mode = False
                        self.lock_message = None
                        return True

                # 3. Check building cards
                cards = self.get_category_cards(self.active_category)
                for i, r in enumerate(self.card_rects):
                    if i < len(cards) and r.collidepoint(mouse_pos):
                        card = cards[i]
                        unlocked, req_text = is_building_unlocked(
                            card["id"], current_science, current_revenue, self.catalogue
                        )
                        if unlocked:
                            self.selected_building = card
                            self.demolish_mode = False
                            self.lock_message = None
                        else:
                            self.selected_building = None
                            self.lock_message = req_text
                        return True

                # Click inside tray absorbed
                if self.tray_rect.collidepoint(mouse_pos):
                    return True

        return False

    def draw(
        self,
        surface: pygame.Surface,
        mouse_pos: tuple[int, int],
        current_science: float = 0.0,
        current_revenue: float = 0.0,
    ) -> None:
        """Render the 50px bottom build tray, category tabs, tier cards, and lock icons."""
        # Tray background (dark panel with 9-slice frame from panel.png)
        tray_surf = pygame.Surface((INTERNAL_WIDTH, 50), pygame.SRCALPHA)
        tray_surf.fill((18, 20, 28, 240))
        surface.blit(tray_surf, self.tray_rect.topleft)
        self.nine_slice(surface, self.tray_rect)

        # 1. Category Tabs
        cat_icons = {
            "generator": ICON.get("cat_generator", 5),
            "cashflow": ICON.get("cat_cashflow", 6),
            "activity": ICON.get("cat_activity", 7),
            "science": ICON.get("cat_science", 8),
        }
        cat_labels = {
            "generator": "Power",
            "cashflow": "Cash",
            "activity": "Fun",
            "science": "Sci",
        }

        for cat, r in self.tab_rects.items():
            is_active = (self.active_category == cat and not self.demolish_mode)
            is_hover = r.collidepoint(mouse_pos)

            bg_col = COLOR_BUTTON_PRESSED if is_active else (COLOR_BUTTON_HOVER if is_hover else COLOR_BUTTON_NORMAL)
            border_col = (255, 220, 50) if is_active else ((140, 145, 160) if is_hover else (80, 85, 100))

            pygame.draw.rect(surface, bg_col, r)
            pygame.draw.rect(surface, border_col, r, 1)

            # Icon
            icon_surf = assets.get_icon(cat_icons.get(cat, 0))
            surface.blit(icon_surf, (r.x + 2, r.y + 1))

            short_lbl = cat_labels.get(cat, cat.capitalize())
            txt = self.font.render(short_lbl, False, COLOR_WHITE)
            surface.blit(txt, (r.x + 19, r.y + 3))

        # 2. Demolish Tool Button
        is_demo_active = self.demolish_mode
        demo_hover = self.demolish_rect.collidepoint(mouse_pos)
        demo_bg = (160, 40, 40) if is_demo_active else (COLOR_BUTTON_HOVER if demo_hover else COLOR_BUTTON_NORMAL)
        demo_border = COLOR_ERROR if is_demo_active else ((160, 165, 180) if demo_hover else (90, 95, 110))

        pygame.draw.rect(surface, demo_bg, self.demolish_rect)
        pygame.draw.rect(surface, demo_border, self.demolish_rect, 1)

        demo_txt = self.font.render("Demolish", False, COLOR_WHITE)
        surface.blit(demo_txt, (self.demolish_rect.x + 4, self.demolish_rect.y + 3))

        # 3. Three Tier Cards
        cards = self.get_category_cards(self.active_category)
        hovered_card_lock_msg: str | None = None

        for i, card in enumerate(cards):
            if i >= len(self.card_rects):
                break
            r = self.card_rects[i]
            unlocked, req_text = is_building_unlocked(
                card["id"], current_science, current_revenue, self.catalogue
            )

            is_selected = (self.selected_building and self.selected_building["id"] == card["id"])
            is_hover = r.collidepoint(mouse_pos)

            if not unlocked and is_hover:
                hovered_card_lock_msg = req_text

            if not unlocked:
                bg_col = (30, 32, 40)
                border_col = (70, 70, 80)
            elif is_selected:
                bg_col = COLOR_BUTTON_PRESSED
                border_col = (80, 220, 80)
            elif is_hover:
                bg_col = COLOR_BUTTON_HOVER
                border_col = (150, 155, 170)
            else:
                bg_col = COLOR_BUTTON_NORMAL
                border_col = (75, 80, 95)

            pygame.draw.rect(surface, bg_col, r)
            pygame.draw.rect(surface, border_col, r, 1)

            # If locked, draw lock icon
            if not unlocked:
                lock_surf = assets.get_icon(ICON.get("locked", 13))
                surface.blit(lock_surf, (r.x + 3, r.y + 3))

                cost_txt = self.font.render(f"${card['cost']}", False, (120, 120, 130))
                cost_x = r.x + r.width - cost_txt.get_width() - 4
                surface.blit(cost_txt, (cost_x, r.y + 4))

                avail_w = cost_x - (r.x + 20) - 2
                name_surf = self._render_card_name(card["name"], avail_w, r.height - 4, (140, 140, 150))
                surface.blit(name_surf, (r.x + 20, r.y + 4))
            else:
                cost_txt = self.font.render(f"${card['cost']}", False, (80, 220, 80))
                cost_x = r.x + r.width - cost_txt.get_width() - 4
                surface.blit(cost_txt, (cost_x, r.y + 4))

                avail_w = cost_x - (r.x + 4) - 2
                name_surf = self._render_card_name(card["name"], avail_w, r.height - 4, COLOR_WHITE)
                surface.blit(name_surf, (r.x + 4, r.y + 4))

        # 4. Lock requirement message banner if hovering or clicking locked card
        active_lock_msg = self.lock_message or hovered_card_lock_msg
        if active_lock_msg:
            from game.ui.widgets import build_text_box
            msg_box = build_text_box(
                active_lock_msg,
                self.font,
                max_width=280,
                nine_slice=self.nine_slice,
                bg_color=(30, 25, 20, 230),
                text_color=(255, 200, 80),
                padding=3,
            )
            bx = max(8, min(INTERNAL_WIDTH - msg_box.get_width() - 8, (INTERNAL_WIDTH - msg_box.get_width()) // 2))
            by = INTERNAL_HEIGHT - 50 - msg_box.get_height() - 4
            surface.blit(msg_box, (bx, by))
