# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Startup sequence logic, timing evaluations, and configuration loader.

This module is pure Python — NO pygame imports allowed.
Manages the sequence of introduction cards (team, art, engine) with linear
alpha fading, inter-card black gaps, and user skip navigation.
"""

from copy import deepcopy
import json
import logging
from pathlib import Path
from typing import Any

from game.constants import (
    SPLASH_FADE_IN,
    SPLASH_FADE_OUT,
    SPLASH_HOLD,
    STARTUP_FILE,
    STARTUP_GAP_SECONDS,
)

logger = logging.getLogger("lunark.startup")


def get_default_cards() -> list[dict[str, Any]]:
    """Return the built-in fallback definition for the three startup cards.

    Returns:
        list[dict[str, Any]]: Default cards list (team, art, engine).
    """
    return [
        {
            "id": "team",
            "logo": "logo/logo.png",
            "scale_mode": "integer",
            "lines": [
                {
                    "text": "LunArk: Genesis",
                    "size": 22,
                    "color": [255, 255, 255],
                }
            ],
            "fade_in": SPLASH_FADE_IN,
            "hold": SPLASH_HOLD,
            "fade_out": SPLASH_FADE_OUT,
        },
        {
            "id": "art",
            "logo": "logo/aseprite.png",
            "scale_mode": "fit",
            "fade_in": 0.3,
            "hold": 1.2,
            "fade_out": 0.3,
            "lines": [
                {
                    "text": "Art, made by humans,",
                    "size": 22,
                    "color": [255, 255, 255],
                },
                {
                    "text": "with Aseprite",
                    "size": 22,
                    "color": [255, 255, 255],
                },
            ],
        },
        {
            "id": "engine",
            "logo": "logo/pygame_ce.png",
            "scale_mode": "fit",
            "fade_in": 0.3,
            "hold": 1.2,
            "fade_out": 0.3,
            "lines": [
                {
                    "text": "Pygame CE",
                    "size": 22,
                    "color": [255, 255, 255],
                }
            ],
        },
    ]


def load_startup_cards(path: Path | None = None) -> list[dict[str, Any]]:
    """Load startup cards from JSON, falling back to defaults if missing or invalid.

    Args:
        path: Path to startup.json. Defaults to constants.STARTUP_FILE.

    Returns:
        list[dict[str, Any]]: Validated list of card dictionary objects.
    """
    target_path = path or STARTUP_FILE
    if not target_path.exists():
        logger.info("Startup file not found at %s. Using default cards.", target_path)
        return get_default_cards()

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            logger.warning("Startup JSON is not a non-empty list. Using defaults.")
            return get_default_cards()

        # Validate that each item is a dict with required fields
        valid_cards: list[dict[str, Any]] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning("Card %d in startup.json is not an object. Reverting to defaults.", i)
                return get_default_cards()

            card = deepcopy(item)
            # Apply default timings if omitted
            if "fade_in" not in card:
                card["fade_in"] = SPLASH_FADE_IN
            if "hold" not in card:
                card["hold"] = SPLASH_HOLD
            if "fade_out" not in card:
                card["fade_out"] = SPLASH_FADE_OUT

            # Ensure scale_mode is valid
            if card.get("scale_mode") not in ("integer", "fit"):
                card["scale_mode"] = "fit"

            valid_cards.append(card)

        return valid_cards

    except Exception as exc:
        logger.warning("Failed loading startup config %s: %s. Using defaults.", target_path, exc)
        return get_default_cards()


def get_card_durations(
    cards: list[dict[str, Any]],
    gap_seconds: float = STARTUP_GAP_SECONDS,
) -> list[float]:
    """Calculate the active duration (fade_in + hold + fade_out) for each card.

    Args:
        cards: List of card configurations.
        gap_seconds: Gap duration in seconds.

    Returns:
        list[float]: Duration in seconds for each card.
    """
    durations: list[float] = []
    for card in cards:
        fi = float(card.get("fade_in", SPLASH_FADE_IN))
        h = float(card.get("hold", SPLASH_HOLD))
        fo = float(card.get("fade_out", SPLASH_FADE_OUT))
        durations.append(fi + h + fo)
    return durations


def evaluate_startup_sequence(
    elapsed: float,
    cards: list[dict[str, Any]],
    gap_seconds: float = STARTUP_GAP_SECONDS,
) -> tuple[int, int, bool, bool]:
    """Evaluate sequence timeline and return current state.

    Args:
        elapsed: Elapsed time in seconds since sequence start.
        cards: List of card configurations.
        gap_seconds: Black gap in seconds between cards.

    Returns:
        tuple[int, int, bool, bool]:
            - active card index (0-based)
            - content alpha (0 to 255)
            - in_gap flag (True if currently in black inter-card gap)
            - is_finished flag (True if all cards and gaps have completed)
    """
    if not cards:
        return (0, 0, False, True)

    if elapsed < 0.0:
        return (0, 0, False, False)

    t = float(elapsed)
    num_cards = len(cards)

    for i, card in enumerate(cards):
        fi = float(card.get("fade_in", SPLASH_FADE_IN))
        h = float(card.get("hold", SPLASH_HOLD))
        fo = float(card.get("fade_out", SPLASH_FADE_OUT))
        card_duration = fi + h + fo

        if t < card_duration:
            # Active in card i
            if t < fi:
                # Fade in phase
                if fi > 0.0:
                    alpha = int(round(255.0 * (t / fi)))
                else:
                    alpha = 255
            elif t < fi + h:
                # Full hold phase
                alpha = 255
            else:
                # Fade out phase
                rem = t - (fi + h)
                if fo > 0.0:
                    alpha = int(round(255.0 * (1.0 - (rem / fo))))
                else:
                    alpha = 0

            clamped_alpha = max(0, min(255, alpha))
            return (i, clamped_alpha, False, False)

        t -= card_duration

        # Inter-card gap (only between cards, not after the final card)
        if i < num_cards - 1:
            if t < (gap_seconds - 1e-7):
                # In gap between card i and card i+1
                return (i, 0, True, False)
            t -= gap_seconds

    # Sequence has fully concluded
    return (num_cards - 1, 0, False, True)


class StartupSequence:
    """Stateful coordinator for advancing and skipping through startup cards."""

    def __init__(
        self,
        cards: list[dict[str, Any]] | None = None,
        gap_seconds: float = STARTUP_GAP_SECONDS,
    ) -> None:
        self.cards: list[dict[str, Any]] = cards if cards is not None else load_startup_cards()
        self.gap_seconds: float = float(gap_seconds)
        self.elapsed: float = 0.0
        self.card_index: int = 0
        self.alpha: int = 0
        self.in_gap: bool = False
        self.is_finished: bool = False

        self._card_start_times: list[float] = []
        self._calculate_timeline()
        self._update_state()

    def _calculate_timeline(self) -> None:
        """Precompute timestamp boundaries for each card."""
        current_time = 0.0
        self._card_start_times = []
        for i, card in enumerate(self.cards):
            self._card_start_times.append(current_time)
            fi = float(card.get("fade_in", SPLASH_FADE_IN))
            h = float(card.get("hold", SPLASH_HOLD))
            fo = float(card.get("fade_out", SPLASH_FADE_OUT))
            current_time += fi + h + fo
            if i < len(self.cards) - 1:
                current_time += self.gap_seconds
        self.total_duration: float = current_time

    def _update_state(self) -> None:
        self.card_index, self.alpha, self.in_gap, self.is_finished = evaluate_startup_sequence(
            self.elapsed, self.cards, self.gap_seconds
        )

    def update(self, dt: float) -> None:
        """Advance timeline by dt seconds."""
        if self.is_finished:
            return
        self.elapsed += max(0.0, float(dt))
        self._update_state()

    def skip_card(self) -> None:
        """Skip currently active card to the start of the next card, or finish."""
        if self.is_finished:
            return

        next_idx = self.card_index + 1
        if next_idx < len(self._card_start_times):
            self.elapsed = self._card_start_times[next_idx] + 1e-5
            self._update_state()
        else:
            self.skip_all()

    def skip_all(self) -> None:
        """Skip entire sequence straight to finish."""
        self.elapsed = self.total_duration
        self.is_finished = True
        self.alpha = 0
        self.in_gap = False
        if self.cards:
            self.card_index = len(self.cards) - 1
