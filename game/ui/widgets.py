# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Reusable UI widgets for LunArk: Genesis.

All widgets are rendered at internal canvas resolution (480x270) using
whole-pixel positions and nearest-neighbor drawing.
"""

from collections.abc import Callable
import pygame

from game.constants import (
    COLOR_BAR_BG,
    COLOR_BAR_BORDER,
    COLOR_BUTTON_BORDER,
    COLOR_BUTTON_DISABLED,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_NORMAL,
    COLOR_BUTTON_PRESSED,
    COLOR_BUTTON_TEXT,
    COLOR_BUTTON_TEXT_DISABLED,
    COLOR_DIALOGUE_BG,
    COLOR_DIALOGUE_BORDER,
    COLOR_INPUT_ACTIVE_BORDER,
    COLOR_INPUT_BG,
    COLOR_INPUT_BORDER,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TOGGLE_KNOB,
    COLOR_TOGGLE_OFF,
    COLOR_TOGGLE_ON,
    COLOR_TOOLTIP_BG,
    COLOR_TOOLTIP_BORDER,
    COLOR_WHITE,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
)


def wrap_text_to_width(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap a text string into multiple lines so no line exceeds max_width."""
    if not text:
        return []
    words = text.split(" ")
    lines: list[str] = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def build_text_box(
    text: str | list[str],
    font: pygame.font.Font,
    max_width: int | None = None,
    nine_slice: Callable[[pygame.Surface, pygame.Rect], None] | None = None,
    bg_color: tuple[int, int, int, int] | tuple[int, int, int] | None = None,
    text_color: tuple[int, int, int] = COLOR_WHITE,
    padding: int | None = None,
) -> pygame.Surface:
    """Measure text, add theme padding, round up to whole pixels, and render with 9-slice frame.

    Shared helper for tray cards, banners, tooltips, info panel, dialogue, and buttons.
    """
    from game.logic.data import load_theme
    import math

    theme_ui = load_theme().get("ui", {})
    pad = int(padding if padding is not None else theme_ui.get("padding", 6))
    limit_w = int(max_width if max_width is not None else theme_ui.get("max_width", 260))

    # Normalize into lines, wrapping if any line exceeds limit_w
    raw_lines: list[str] = [text] if isinstance(text, str) else list(text)
    wrapped_lines: list[str] = []
    for line in raw_lines:
        wrapped_lines.extend(wrap_text_to_width(str(line), font, limit_w))

    if not wrapped_lines:
        wrapped_lines = [""]

    text_w = max(font.size(line)[0] for line in wrapped_lines)
    line_h = font.get_linesize()
    text_h = len(wrapped_lines) * line_h

    # Add padding and round up to whole pixels
    total_w = int(math.ceil(text_w + pad * 2))
    total_h = int(math.ceil(text_h + pad * 2))

    box_w = max(16, total_w)
    box_h = max(16, total_h)

    surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)

    # 1. Background fill
    fill_col = bg_color if bg_color is not None else tuple(theme_ui.get("panel_bg", [20, 22, 32, 225]))
    surf.fill(fill_col)

    # 2. 9-slice frame
    if nine_slice is not None:
        nine_slice(surf, surf.get_rect())

    # 3. Text lines
    curr_y = pad
    for line in wrapped_lines:
        line_surf = font.render(line, False, text_color)
        surf.blit(line_surf, (pad, curr_y))
        curr_y += line_h

    return surf


class Label:
    """Simple text label rendered at whole-pixel coordinates."""

    def __init__(
        self,
        x: int,
        y: int,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int] = COLOR_WHITE,
        anchor: str = "topleft",
    ) -> None:
        self.x = int(x)
        self.y = int(y)
        self.text = text
        self.font = font
        self.color = color
        self.anchor = anchor
        self._rendered = self.font.render(self.text, False, self.color)
        self.rect = self._compute_rect()

    def _compute_rect(self) -> pygame.Rect:
        rect = self._rendered.get_rect()
        setattr(rect, self.anchor, (self.x, self.y))
        return rect

    def set_text(self, text: str) -> None:
        """Update label text and refresh rendered texture."""
        if text != self.text:
            self.text = text
            self._rendered = self.font.render(self.text, False, self.color)
            self.rect = self._compute_rect()

    def draw(self, surface: pygame.Surface) -> None:
        """Render label onto target canvas."""
        surface.blit(self._rendered, self.rect)


class Button:
    """Clickable 9-slice or flat-bordered button with 4 distinct visual states."""

    def __init__(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        text: str,
        font: pygame.font.Font,
        callback: Callable[[], None] | None = None,
        enabled: bool = True,
    ) -> None:
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.text = text
        self.font = font
        self.callback = callback
        self.enabled = enabled

        self.hovered = False
        self.pressed = False
        self.clicked = False
        self.nine_slice: Callable[[pygame.Surface, pygame.Rect], None] | None = None

    def set_nine_slice(self, draw_func: Callable[[pygame.Surface, pygame.Rect], None] | None) -> None:
        """Attach a 9-slice draw function for custom button art."""
        self.nine_slice = draw_func

    def update(self, events: list[pygame.event.Event], mouse_pos: tuple[int, int]) -> None:
        """Update hover/pressed state and detect click on button release."""
        self.clicked = False
        if not self.enabled:
            self.hovered = False
            self.pressed = False
            return

        self.hovered = self.rect.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered:
                    self.pressed = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.pressed and self.hovered:
                    self.clicked = True
                    try:
                        from game.audio import audio
                        audio.play("click")
                    except Exception:
                        pass
                    if self.callback:
                        self.callback()
                self.pressed = False

    def draw(self, surface: pygame.Surface) -> None:
        """Render button based on current state using button.png 9-slice states."""
        if not self.enabled:
            st = 3
            bg_col = COLOR_BUTTON_DISABLED
            txt_col = COLOR_BUTTON_TEXT_DISABLED
        elif self.pressed:
            st = 2
            bg_col = COLOR_BUTTON_PRESSED
            txt_col = COLOR_BUTTON_TEXT
        elif self.hovered:
            st = 1
            bg_col = COLOR_BUTTON_HOVER
            txt_col = COLOR_WHITE
        else:
            st = 0
            bg_col = COLOR_BUTTON_NORMAL
            txt_col = COLOR_BUTTON_TEXT

        # Base background fill
        pygame.draw.rect(surface, bg_col, self.rect)

        # 9-slice frame from button.png (4 states side by side, 8px corners)
        from game.assets import assets
        btn_slices = assets.get_button_slices()
        if btn_slices and st < len(btn_slices):
            btn_slices[st](surface, self.rect)
        elif self.nine_slice:
            self.nine_slice(surface, self.rect)
        else:
            border_col = COLOR_BUTTON_DISABLED if not self.enabled else COLOR_BUTTON_BORDER
            pygame.draw.rect(surface, border_col, self.rect, 1)

        # Centered text
        txt_surf = self.font.render(self.text, False, txt_col)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        # Shift text down by 1px when pressed for tactile button feedback
        if self.pressed and self.enabled:
            txt_rect.y += 1
        surface.blit(txt_surf, txt_rect)


class Toggle:
    """Binary switch toggle widget with animated state indicator."""

    def __init__(
        self,
        x: int,
        y: int,
        label_text: str,
        font: pygame.font.Font,
        value: bool = False,
        callback: Callable[[bool], None] | None = None,
    ) -> None:
        self.x = int(x)
        self.y = int(y)
        self.label_text = label_text
        self.font = font
        self.value = value
        self.callback = callback

        self.pill_rect = pygame.Rect(self.x, self.y + 1, 24, 12)
        self.text_surf = self.font.render(self.label_text, False, COLOR_BUTTON_TEXT)

    def update(self, events: list[pygame.event.Event], mouse_pos: tuple[int, int]) -> None:
        """Toggle value on click over the pill or label."""
        hit_h = max(14, self.text_surf.get_height())
        hit_rect = pygame.Rect(self.x, self.y, 24 + 6 + self.text_surf.get_width(), hit_h)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hit_rect.collidepoint(mouse_pos):
                    self.value = not self.value
                    if self.callback:
                        self.callback(self.value)

    def draw(self, surface: pygame.Surface) -> None:
        """Render toggle switch pill and label using toggle.png."""
        from game.assets import assets
        toggle_surf = assets.load_image("toggle", default_size=(48, 12))
        if "toggle" not in assets.missing and toggle_surf.get_width() >= 48:
            sub_x = 24 if self.value else 0
            sub = toggle_surf.subsurface(pygame.Rect(sub_x, 0, 24, 12))
            surface.blit(sub, self.pill_rect.topleft)
        else:
            pill_bg = COLOR_TOGGLE_ON if self.value else COLOR_TOGGLE_OFF
            pygame.draw.rect(surface, pill_bg, self.pill_rect, border_radius=6)
            pygame.draw.rect(surface, (40, 40, 50), self.pill_rect, 1, border_radius=6)

            # Sliding circular knob (10x10)
            knob_x = self.pill_rect.right - 11 if self.value else self.pill_rect.left + 1
            knob_rect = pygame.Rect(knob_x, self.pill_rect.top + 1, 10, 10)
            pygame.draw.ellipse(surface, COLOR_TOGGLE_KNOB, knob_rect)

        # Label text vertically aligned with pill center
        surface.blit(self.text_surf, (self.pill_rect.right + 6, self.y))


class OptionSelector:
    """Cyclic option picker with < and > directional buttons."""

    def __init__(
        self,
        x: int,
        y: int,
        w: int,
        label_text: str,
        options: list[str],
        font: pygame.font.Font,
        selected_index: int = 0,
        callback: Callable[[int, str], None] | None = None,
        enabled: bool = True,
    ) -> None:
        self.rect = pygame.Rect(int(x), int(y), int(w), 16)
        self.label_text = label_text
        self.options = options
        self.font = font
        self.selected_index = max(0, min(selected_index, len(options) - 1)) if options else 0
        self.callback = callback
        self.enabled = enabled
        self.note: str | None = None

        # Arrow hitboxes (each 12x14 px)
        self.btn_left_rect = pygame.Rect(self.rect.right - 110, self.rect.y + 1, 12, 14)
        self.btn_right_rect = pygame.Rect(self.rect.right - 14, self.rect.y + 1, 12, 14)

    def get_value(self) -> str:
        """Get currently selected option string."""
        if not self.options:
            return ""
        return self.options[self.selected_index]

    def set_index(self, index: int) -> None:
        """Explicitly set active index."""
        if self.options:
            self.selected_index = max(0, min(index, len(self.options) - 1))

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable interaction."""
        self.enabled = enabled

    def set_note(self, note: str | None) -> None:
        """Set informational hint text rendered below when disabled."""
        self.note = note

    def update(self, events: list[pygame.event.Event], mouse_pos: tuple[int, int]) -> None:
        """Handle directional arrow clicks."""
        if not self.enabled or not self.options:
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_left_rect.collidepoint(mouse_pos):
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                    if self.callback:
                        self.callback(self.selected_index, self.get_value())
                elif self.btn_right_rect.collidepoint(mouse_pos):
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                    if self.callback:
                        self.callback(self.selected_index, self.get_value())

    def draw(self, surface: pygame.Surface) -> None:
        """Render label, arrows, and current option value."""
        txt_col = COLOR_BUTTON_TEXT if self.enabled else COLOR_BUTTON_TEXT_DISABLED
        label_surf = self.font.render(self.label_text, False, txt_col)
        surface.blit(label_surf, (self.rect.x, self.rect.y + 2))

        val_col = COLOR_WHITE if self.enabled else COLOR_BUTTON_TEXT_DISABLED
        current_text = self.get_value()
        val_surf = self.font.render(current_text, False, val_col)
        # Center option text between arrows
        mid_x = (self.btn_left_rect.right + self.btn_right_rect.left) // 2
        val_rect = val_surf.get_rect(center=(mid_x, self.rect.y + 8))
        surface.blit(val_surf, val_rect)

        # Draw left and right arrows
        arrow_col = COLOR_WHITE if self.enabled else COLOR_BUTTON_TEXT_DISABLED
        l_surf = self.font.render("<", False, arrow_col)
        r_surf = self.font.render(">", False, arrow_col)
        surface.blit(l_surf, l_surf.get_rect(center=self.btn_left_rect.center))
        surface.blit(r_surf, r_surf.get_rect(center=self.btn_right_rect.center))

        # Render disabled explanatory note if provided
        if not self.enabled and self.note:
            note_surf = self.font.render(self.note, False, (140, 140, 150))
            surface.blit(note_surf, (self.rect.x, self.rect.y + 14))


class ProgressBar:
    """Visual meter with proportion fill and low-value flashing alert."""

    def __init__(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: tuple[int, int, int],
        max_value: float = 100.0,
        value: float = 0.0,
        show_text: bool = False,
        font: pygame.font.Font | None = None,
    ) -> None:
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.color = color
        self.max_value = max(1.0, float(max_value))
        self.value = float(value)
        self.show_text = show_text
        self.font = font
        self.flashing = False

    def set_value(self, value: float) -> None:
        """Update progress value."""
        self.value = max(0.0, min(float(value), self.max_value))

    def set_flashing(self, flashing: bool) -> None:
        """Turn on/off low-threshold warning flash."""
        self.flashing = flashing

    def draw(self, surface: pygame.Surface) -> None:
        """Render progress bar frame and filled rect."""
        pygame.draw.rect(surface, COLOR_BAR_BG, self.rect)

        ratio = self.value / self.max_value
        fill_w = int((self.rect.width - 2) * ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x + 1, self.rect.y + 1, fill_w, self.rect.height - 2)
            fill_col = (255, 60, 60) if self.flashing else self.color
            pygame.draw.rect(surface, fill_col, fill_rect)

        pygame.draw.rect(surface, COLOR_BAR_BORDER, self.rect, 1)

        if self.show_text and self.font:
            txt = f"{int(self.value)}/{int(self.max_value)}"
            txt_surf = self.font.render(txt, False, COLOR_WHITE)
            txt_rect = txt_surf.get_rect(center=self.rect.center)
            surface.blit(txt_surf, txt_rect)


class Panel:
    """Rounded or bordered background surface for grouping interface elements using panel.png."""

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        from game.assets import assets, make_nine_slice
        panel_surf = assets.load_image("panel", default_size=(24, 24))
        self.nine_slice: Callable[[pygame.Surface, pygame.Rect], None] | None = make_nine_slice(panel_surf, corner=8)

    def set_nine_slice(self, draw_func: Callable[[pygame.Surface, pygame.Rect], None] | None) -> None:
        """Set optional custom 9-slice drawer."""
        self.nine_slice = draw_func

    def draw(self, surface: pygame.Surface) -> None:
        """Render panel onto destination surface."""
        panel_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surf.fill(COLOR_PANEL_BG)
        surface.blit(panel_surf, self.rect.topleft)
        if self.nine_slice:
            self.nine_slice(surface, self.rect)
        else:
            pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1, border_radius=4)


class DialogueBox:
    """Story dialogue box supporting typewriter text and advance cues using dialogue_box.png."""

    def __init__(self, x: int, y: int, w: int, h: int, font: pygame.font.Font) -> None:
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.font = font
        self.full_text = ""
        self.displayed_chars = 0
        self.char_timer = 0.0
        self.speed = 0.03  # seconds per character

        self.text_complete = False
        self.finished = False
        self.blink_timer = 0.0

        from game.assets import assets, make_nine_slice
        box_surf = assets.load_image("dialogue_box", default_size=(24, 24))
        self.nine_slice: Callable[[pygame.Surface, pygame.Rect], None] | None = make_nine_slice(box_surf, corner=8)

    def set_text(self, text: str, speed: float = 0.03) -> None:
        """Start typewriter effect with given string."""
        self.full_text = text
        self.displayed_chars = 0
        self.char_timer = 0.0
        self.speed = speed
        self.text_complete = False
        self.finished = False

    def update(self, dt: float, events: list[pygame.event.Event]) -> None:
        """Advance typewriter timer and process skip/continue inputs."""
        self.blink_timer += dt

        # Increment characters
        if not self.text_complete:
            self.char_timer += dt
            chars_to_add = int(self.char_timer / self.speed)
            if chars_to_add > 0:
                self.displayed_chars = min(len(self.full_text), self.displayed_chars + chars_to_add)
                self.char_timer %= self.speed
                if self.displayed_chars >= len(self.full_text):
                    self.text_complete = True

        # Input to fast-forward or advance
        for event in events:
            advances = False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                advances = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                advances = True

            if advances:
                if not self.text_complete:
                    # Skip typewriter directly to full line
                    self.displayed_chars = len(self.full_text)
                    self.text_complete = True
                else:
                    # Signal line completed
                    self.finished = True

    def draw(self, surface: pygame.Surface) -> None:
        """Render dialogue background, wrapped typewriter text, and advance cue."""
        box_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        box_surf.fill(COLOR_DIALOGUE_BG)
        surface.blit(box_surf, self.rect.topleft)

        if self.nine_slice:
            self.nine_slice(surface, self.rect)
        else:
            pygame.draw.rect(surface, COLOR_DIALOGUE_BORDER, self.rect, 1, border_radius=4)

        # Word wrap typewriter text
        visible_str = self.full_text[:self.displayed_chars]
        words = visible_str.split(" ")
        lines: list[str] = []
        cur_line = ""
        max_w = self.rect.width - 24

        for word in words:
            test_line = f"{cur_line} {word}".strip()
            if self.font.size(test_line)[0] <= max_w:
                cur_line = test_line
            else:
                lines.append(cur_line)
                cur_line = word
        if cur_line:
            lines.append(cur_line)

        # Draw lines
        line_y = self.rect.y + 8
        for line in lines:
            line_surf = self.font.render(line, False, COLOR_WHITE)
            surface.blit(line_surf, (self.rect.x + 10, line_y))
            line_y += self.font.get_linesize()

        # Blinking prompt arrow when text is ready to advance (uses next_arrow.png if available)
        if self.text_complete and int(self.blink_timer * 3) % 2 == 0:
            from game.assets import assets
            arrow_surf = assets.get_next_arrow(int(self.blink_timer * 30))
            if arrow_surf:
                surface.blit(arrow_surf, (self.rect.right - 14, self.rect.bottom - 12))
            else:
                arrow = self.font.render(">", False, (220, 220, 240))
                surface.blit(arrow, (self.rect.right - 14, self.rect.bottom - 14))


class TextInput:
    """Single-line keyboard input box for player character names."""

    def __init__(
        self,
        x: int,
        y: int,
        w: int,
        font: pygame.font.Font,
        max_length: int = 12,
        default_text: str = "",
        placeholder: str = "",
    ) -> None:
        self.rect = pygame.Rect(int(x), int(y), int(w), 18)
        self.font = font
        self.max_length = max_length
        self.text = default_text
        self.placeholder = placeholder
        self.active = True
        self.done = False
        self.cursor_timer = 0.0

    def update(self, dt: float, events: list[pygame.event.Event], mouse_pos: tuple[int, int]) -> None:
        """Handle typing, backspace, and enter submission."""
        self.cursor_timer += dt
        self.done = False

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.active = self.rect.collidepoint(mouse_pos)

            elif self.active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.done = True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif len(self.text) < self.max_length and event.unicode.isprintable() and event.unicode != "":
                    self.text += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        """Render input frame and active text with cursor."""
        pygame.draw.rect(surface, COLOR_INPUT_BG, self.rect)
        border_col = COLOR_INPUT_ACTIVE_BORDER if self.active else COLOR_INPUT_BORDER
        pygame.draw.rect(surface, border_col, self.rect, 1)

        display_text = self.text if self.text else self.placeholder
        text_col = COLOR_WHITE if self.text else (120, 120, 130)
        txt_surf = self.font.render(display_text, False, text_col)
        surface.blit(txt_surf, (self.rect.x + 4, self.rect.y + 3))

        # Blinking cursor
        if self.active and int(self.cursor_timer * 2) % 2 == 0:
            cursor_x = self.rect.x + 4 + self.font.size(self.text)[0]
            pygame.draw.line(
                surface,
                COLOR_WHITE,
                (cursor_x, self.rect.y + 3),
                (cursor_x, self.rect.bottom - 3),
                1,
            )


class Tooltip:
    """Contextual floating info balloon anchored to mouse cursor coordinates using panel.png."""

    def __init__(self, font: pygame.font.Font) -> None:
        self.font = font
        self.lines: list[str] = []
        self.visible = False
        self.x = 0
        self.y = 0
        from game.assets import assets, make_nine_slice
        panel_surf = assets.load_image("panel", default_size=(24, 24))
        self.nine_slice: Callable[[pygame.Surface, pygame.Rect], None] | None = make_nine_slice(panel_surf, corner=8)

    def show(self, text: str, x: int, y: int) -> None:
        """Position and show tooltip."""
        self.lines = [text] if text else []
        self.x = int(x)
        self.y = int(y)
        self.visible = bool(self.lines)

    def show_multiline(self, lines: list[str], pos: tuple[int, int]) -> None:
        """Position and show tooltip with multiple lines of text."""
        self.lines = [str(line) for line in lines if line]
        self.x = int(pos[0])
        self.y = int(pos[1])
        self.visible = bool(self.lines)

    def hide(self) -> None:
        """Hide tooltip."""
        self.visible = False

    def draw(self, surface: pygame.Surface) -> None:
        """Render tooltip bubble clamped inside canvas boundaries."""
        if not self.visible or not self.lines:
            return

        box_surf = build_text_box(
            self.lines,
            self.font,
            max_width=220,
            nine_slice=self.nine_slice,
            bg_color=COLOR_TOOLTIP_BG,
            padding=4,
        )
        w = box_surf.get_width()
        h = box_surf.get_height()

        # Position slightly offset from mouse
        tx = self.x + 8
        ty = self.y + 8

        # Screen clamp
        if tx + w > INTERNAL_WIDTH - 2:
            tx = self.x - w - 2
        if ty + h > INTERNAL_HEIGHT - 2:
            ty = self.y - h - 2

        surface.blit(box_surf, (max(2, tx), max(2, ty)))
