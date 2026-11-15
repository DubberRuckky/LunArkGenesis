# Written with Claude in Antigravity (continuation after previous model). Reviewed by LunArk team.
"""Intro / Tutorial screen for LunArk: Genesis.

Shows Lieutenant Vance's portrait and dialogue, asks for the Commander's
name, then walks through 6 guided tutorial steps before handing control
to the main GameScreen.

Design rules:
- NO hard-coded layout numbers: padding and sizes come from theme.json.
- All on-screen words come from tutorial.json.
- Mentor portrait: img/characters/mentor.png (256x64, four 64x64 expressions).
- Strictly NO logic imports from pygame.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
import pygame

from game.assets import assets
from game.constants import (
    COLOR_BLACK,
    COLOR_DARK_GREY,
    COLOR_DIALOGUE_BG,
    COLOR_DIALOGUE_BORDER,
    COLOR_WHITE,
    COLOR_ENERGY,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_TITLE,
)
from game.logic.data import load_text, load_theme
from game.logic.tutorial import TutorialManager
from game.ui.widgets import Button, TextInput

if TYPE_CHECKING:
    pass

# Mentor portrait is a 256x64 horizontal strip of four 64x64 expressions.
MENTOR_FRAME_W = 64
MENTOR_FRAME_H = 64

# Dialogue box geometry (all relative to canvas, so it always fits 480x270).
BOX_X = 10
BOX_Y = INTERNAL_HEIGHT - 90
BOX_W = INTERNAL_WIDTH - 20
BOX_H = 84

# Pulsing highlight colour
HIGHLIGHT_ALPHA = 120   # 0-255


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    """Split a string into lines that each fit within max_w pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if font.size(trial)[0] <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


class IntroScreen:
    """Mentor-guided intro and 6-step tutorial before the game begins."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.theme = load_theme()
        self.text_data = load_text()

        self.font = assets.get_font(FONT_SIZE_MEDIUM)
        self.small_font = assets.get_font(FONT_SIZE_SMALL)
        self.title_font = assets.get_font(FONT_SIZE_LARGE)

        self.tutorial = TutorialManager()

        # Mentor expression sub-surfaces cache (lazy; None until first draw)
        self._mentor_frames: list[pygame.Surface] | None = None

        # Name-entry widget (step 0)
        self.name_input = TextInput(
            BOX_X + 100,
            BOX_Y + 44,
            BOX_W - 120,
            self.font,
            max_length=self.tutorial.max_name_length,
            default_text="",
            placeholder="Commander",
        )

        # Dialogue line index (how far into current step's dialogue we are)
        self._dialogue_line: int = 0

        # Pulsing highlight timer
        self._pulse_timer: float = 0.0

        # Glossary overlay state
        self._show_glossary: bool = False
        self._glossary_scroll: int = 0

        # Build persistent buttons (layout along bottom of dialogue box)
        btn_y = BOX_Y + BOX_H - 22
        self._btn_next = Button(
            INTERNAL_WIDTH - 90,
            btn_y,
            80,
            18,
            "Next >",
            self.font,
            callback=self._on_next,
        )
        self._btn_skip = Button(
            BOX_X,
            btn_y,
            60,
            18,
            "Skip",
            self.font,
            callback=self._on_skip,
        )
        self._btn_glossary = Button(
            BOX_X + 66,
            btn_y,
            70,
            18,
            "Glossary",
            self.font,
            callback=self._on_toggle_glossary,
        )
        self._btn_close_glossary = Button(
            INTERNAL_WIDTH - 90,
            BOX_Y - 24,
            80,
            18,
            "Close",
            self.font,
            callback=self._on_toggle_glossary,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_mentor_frame(self, expression: int) -> pygame.Surface:
        """Return the mentor portrait surface for the given expression index."""
        if self._mentor_frames is None:
            sheet = assets.load_image("mentor", default_size=(256, 64))
            self._mentor_frames = []
            for i in range(4):
                sub = sheet.subsurface(pygame.Rect(i * MENTOR_FRAME_W, 0, MENTOR_FRAME_W, MENTOR_FRAME_H))
                self._mentor_frames.append(sub.copy())
        idx = max(0, min(3, expression))
        return self._mentor_frames[idx]

    def _current_dialogue(self) -> list[str]:
        info = self.tutorial.get_current_info()
        return info.get("dialogue", [])

    def _current_line(self) -> str:
        lines = self._current_dialogue()
        if not lines:
            return ""
        return lines[min(self._dialogue_line, len(lines) - 1)]

    def _is_last_dialogue_line(self) -> bool:
        lines = self._current_dialogue()
        return self._dialogue_line >= len(lines) - 1

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------

    def _on_next(self) -> None:
        """Advance dialogue line, then advance step when all lines shown."""
        info = self.tutorial.get_current_info()
        step = info.get("step", 0)

        # Step 0: validate name input before proceeding
        if step == 0:
            name = self.name_input.text.strip() or "Commander"
            self.tutorial.set_player_name(name)

        lines = self._current_dialogue()
        if self._dialogue_line < len(lines) - 1:
            # More lines to show in this step
            self._dialogue_line += 1
        else:
            # Advance to next step
            self.tutorial.advance_step()
            self._dialogue_line = 0

            # If tutorial just finished (step 7 → 8), launch game
            if not self.tutorial.is_active:
                self._launch_game()

    def _on_skip(self) -> None:
        """Skip tutorial immediately and launch game."""
        self.tutorial.skip()
        self._launch_game()

    def _on_toggle_glossary(self) -> None:
        self._show_glossary = not self._show_glossary
        self._glossary_scroll = 0

    def _launch_game(self) -> None:
        """Hand control to GameScreen, passing the player name."""
        if hasattr(self.app, "start_game_with_name"):
            self.app.start_game_with_name(self.tutorial.player_name)  # type: ignore[attr-defined]
        elif hasattr(self.app, "set_screen"):
            self.app.set_screen("game")  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Event / Update / Draw
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        mouse_pos = self.app.get_canvas_mouse_pos()  # type: ignore[attr-defined]

        # Glossary overlay intercepts
        if self._show_glossary:
            self._btn_close_glossary.update(events, mouse_pos)
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._show_glossary = False
                elif event.type == pygame.MOUSEWHEEL:
                    self._glossary_scroll = max(0, self._glossary_scroll - event.y)
            return

        info = self.tutorial.get_current_info()
        step = info.get("step", 0)

        # Step 0: name input
        if step == 0:
            self.name_input.update(1 / 60, events, mouse_pos)
            if self.name_input.done:
                self._on_next()
                return

        # Buttons
        self._btn_next.update(events, mouse_pos)
        self._btn_skip.update(events, mouse_pos)
        self._btn_glossary.update(events, mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._on_next()
                elif event.key == pygame.K_ESCAPE:
                    self._on_skip()
                elif event.key == pygame.K_g:
                    self._on_toggle_glossary()

    def update(self, dt: float) -> None:
        self._pulse_timer += dt

    def draw(self, surface: pygame.Surface) -> None:
        # Dark lunar sky background
        surface.fill((6, 6, 10))

        # Procedural stars
        for sx, sy in [(30, 20), (100, 55), (200, 30), (350, 70), (430, 25), (60, 90), (280, 48)]:
            surface.set_at((sx, sy), (200, 200, 215))

        info = self.tutorial.get_current_info()
        step = info.get("step", 0)
        expression = info.get("expression", 0)
        title = info.get("title", "")

        # -- Pulsing highlight (semi-transparent rect) over the target area --
        target = info.get("target")
        if target and not self._show_glossary:
            self._draw_highlight(surface, target)

        # -- Mentor portrait --
        portrait = self._get_mentor_frame(expression)
        p_x = BOX_X + 4
        p_y = BOX_Y - MENTOR_FRAME_H + 4
        surface.blit(portrait, (p_x, p_y))

        # -- Dialogue box background --
        box_surf = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
        box_surf.fill(COLOR_DIALOGUE_BG)
        pygame.draw.rect(box_surf, COLOR_DIALOGUE_BORDER, box_surf.get_rect(), 1)
        surface.blit(box_surf, (BOX_X, BOX_Y))

        # -- Step counter (top-right of box) --
        total_steps = len(self.tutorial.steps)
        if 1 <= step <= total_steps:
            counter_txt = f"Step {step}/{total_steps}"
            c_surf = self.small_font.render(counter_txt, False, (140, 150, 170))
            surface.blit(c_surf, (BOX_X + BOX_W - c_surf.get_width() - 6, BOX_Y + 4))

        # -- Step title --
        title_surf = self.font.render(title, False, COLOR_ENERGY)
        surface.blit(title_surf, (BOX_X + MENTOR_FRAME_W + 8, BOX_Y + 4))

        # -- Dialogue / name input --
        inner_x = BOX_X + MENTOR_FRAME_W + 8
        inner_w = BOX_W - MENTOR_FRAME_W - 16

        if step == 0:
            # Name prompt
            prompt = info.get("dialogue", ["What is your name, Commander?"])[0]
            p_surf = self.font.render(prompt, False, COLOR_WHITE)
            surface.blit(p_surf, (inner_x, BOX_Y + 18))
            self.name_input.rect.x = inner_x
            self.name_input.rect.w = inner_w
            self.name_input.draw(surface)
        else:
            # Dialogue line(s)
            line = self._current_line()
            wrapped = _wrap_text(line, self.font, inner_w)
            y_off = BOX_Y + 18
            for ln in wrapped[:3]:  # max 3 visual lines per tick
                lsurf = self.font.render(ln, False, COLOR_WHITE)
                surface.blit(lsurf, (inner_x, y_off))
                y_off += 13

        # -- "Press Space / Enter" hint --
        if not self._is_last_dialogue_line() or step == 0:
            hint_col = (120, 125, 140)
        else:
            hint_col = (180, 185, 200)
        hint_txt = self.small_font.render("SPACE or ENTER to continue", False, hint_col)
        surface.blit(hint_txt, (inner_x, BOX_Y + BOX_H - 32))

        # -- Buttons --
        self._btn_next.draw(surface)
        self._btn_skip.draw(surface)
        self._btn_glossary.draw(surface)

        # -- Glossary overlay --
        if self._show_glossary:
            self._draw_glossary(surface)

    def _draw_highlight(self, surface: pygame.Surface, target: str) -> None:
        """Draw a pulsing coloured border around the UI region named by target."""
        alpha = int(80 + 40 * abs(pygame.math.Vector2(1, 0).rotate(self._pulse_timer * 120).x))

        # Map target names to approximate canvas regions
        regions: dict[str, tuple[int, int, int, int]] = {
            "hud": (0, 0, INTERNAL_WIDTH, 24),
            "habitat": (272, 24, 80, INTERNAL_HEIGHT - 24 - 50),  # rough centre of world
            "build_fuel_cell": (0, INTERNAL_HEIGHT - 50, INTERNAL_WIDTH // 2, 50),
            "build_datacentre": (0, INTERNAL_HEIGHT - 50, INTERNAL_WIDTH // 2, 50),
            "day_night_clock": (INTERNAL_WIDTH - 90, 0, 90, 24),
            "goal_planet_stats": (0, INTERNAL_HEIGHT - 50, INTERNAL_WIDTH, 50),
            "name_input": (BOX_X + 70, BOX_Y + 42, BOX_W - 90, 20),
            "badge": (INTERNAL_WIDTH // 2 - 60, INTERNAL_HEIGHT // 2 - 20, 120, 40),
        }
        rect_data = regions.get(target)
        if not rect_data:
            return
        hl = pygame.Surface((rect_data[2], rect_data[3]), pygame.SRCALPHA)
        hl.fill((255, 220, 50, alpha))
        pygame.draw.rect(hl, (255, 220, 50, 220), hl.get_rect(), 2)
        surface.blit(hl, (rect_data[0], rect_data[1]))

    def _draw_glossary(self, surface: pygame.Surface) -> None:
        """Render the science glossary overlay panel."""
        gl = self.tutorial.get_glossary()
        panel_w, panel_h = INTERNAL_WIDTH - 40, INTERNAL_HEIGHT - 60
        px, py = 20, 30

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((14, 16, 28, 240))
        pygame.draw.rect(panel_surf, (100, 110, 150), panel_surf.get_rect(), 1)
        surface.blit(panel_surf, (px, py))

        hdr = self.title_font.render("Science Glossary", False, COLOR_ENERGY)
        surface.blit(hdr, (px + 8, py + 6))

        y = py + 30
        line_h = 24
        visible = (panel_h - 50) // line_h
        for entry in gl[self._glossary_scroll: self._glossary_scroll + visible]:
            term_surf = self.font.render(entry["term"] + ":", False, (140, 200, 255))
            surface.blit(term_surf, (px + 8, y))
            # Wrap definition
            def_lines = _wrap_text(entry["definition"], self.small_font, panel_w - 20)
            dy = y + 12
            for dl in def_lines[:2]:
                d_surf = self.small_font.render(dl, False, (200, 200, 210))
                surface.blit(d_surf, (px + 12, dy))
                dy += 11
            y += line_h + (len(def_lines) - 1) * 11

        self._btn_close_glossary.draw(surface)
        # Scroll hint
        if len(gl) > visible:
            sh = self.small_font.render("Scroll: mouse wheel", False, (100, 110, 130))
            surface.blit(sh, (px + 8, py + panel_h - 16))
