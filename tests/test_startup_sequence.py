# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Unit tests for game/logic/startup_sequence.py.

All tests here verify pure Python logic without initializing Pygame.
"""

from pathlib import Path
import pytest

from game.constants import SPLASH_FADE_IN, SPLASH_FADE_OUT, SPLASH_HOLD
from game.logic.startup_sequence import (
    StartupSequence,
    evaluate_startup_sequence,
    get_default_cards,
    load_startup_cards,
)


def test_t_zero_nothing_visible() -> None:
    """Verifies that at t=0, alpha is 0 (nothing visible) and sequence is not finished."""
    cards = get_default_cards()
    card_idx, alpha, in_gap, is_finished = evaluate_startup_sequence(0.0, cards)
    assert card_idx == 0
    assert alpha == 0
    assert in_gap is False
    assert is_finished is False


def test_mid_hold_alpha_255() -> None:
    """Verifies that in the middle of a card's hold phase, alpha is 255."""
    cards = get_default_cards()
    # Card 0: fade_in = 0.5, hold = 1.5. Mid-hold is at 0.5 + 0.75 = 1.25s
    mid_hold_t = SPLASH_FADE_IN + (SPLASH_HOLD / 2.0)
    card_idx, alpha, in_gap, is_finished = evaluate_startup_sequence(mid_hold_t, cards)
    assert card_idx == 0
    assert alpha == 255
    assert in_gap is False
    assert is_finished is False


def test_alpha_always_within_bounds() -> None:
    """Verifies that alpha is strictly in [0, 255] for arbitrary timestamps."""
    cards = get_default_cards()
    # Sample every 0.05 seconds across the full sequence
    for t_step in range(0, 160):
        t = t_step * 0.05
        _, alpha, _, _ = evaluate_startup_sequence(t, cards)
        assert 0 <= alpha <= 255, f"Alpha out of range at t={t}: {alpha}"


def test_cards_run_in_order_and_finish() -> None:
    """Verifies that cards run in sequential order (0, 1, 2) and sequence finishes."""
    cards = get_default_cards()
    seq = StartupSequence(cards=cards, gap_seconds=0.15)

    observed_cards = []
    # Step through sequence in 0.1s increments
    for _ in range(100):
        if not seq.in_gap and seq.card_index not in observed_cards:
            observed_cards.append(seq.card_index)
        seq.update(0.1)
        if seq.is_finished:
            break

    assert observed_cards == [0, 1, 2]
    assert seq.is_finished is True


def test_per_card_timing_overrides_and_defaults() -> None:
    """Verifies that per-card timing overrides work, and missing keys use SPLASH_ constants."""
    custom_cards = [
        {"id": "c1", "lines": []},  # No timings -> defaults
        {"id": "c2", "fade_in": 0.2, "hold": 0.4, "fade_out": 0.2, "lines": []},  # Overrides
    ]

    # Card 1 defaults
    c1_dur = SPLASH_FADE_IN + SPLASH_HOLD + SPLASH_FADE_OUT
    # t at c1 mid-fade-in
    _, alpha_fade, _, _ = evaluate_startup_sequence(SPLASH_FADE_IN / 2.0, custom_cards)
    assert 0 < alpha_fade < 255

    # Card 2 starts at c1_dur + 0.15 gap
    gap = 0.15
    c2_start = c1_dur + gap
    # Mid-hold of c2: c2_start + 0.2 (fade) + 0.2 (mid-hold) = c2_start + 0.4
    card_idx, alpha_c2, in_gap, is_finished = evaluate_startup_sequence(c2_start + 0.4, custom_cards, gap)
    assert card_idx == 1
    assert alpha_c2 == 255
    assert in_gap is False
    assert is_finished is False

    # After c2 completes (c2 duration is 0.8s)
    c2_end = c2_start + 0.8
    _, _, _, finished = evaluate_startup_sequence(c2_end + 0.01, custom_cards, gap)
    assert finished is True


def test_huge_dt_jump_does_not_crash_or_skip_wrongly() -> None:
    """Verifies that massive delta time jumps resolve cleanly to finished state without error."""
    cards = get_default_cards()
    seq = StartupSequence(cards=cards)

    # Jump forward by 10,000 seconds in a single frame
    seq.update(10000.0)
    assert seq.is_finished is True
    assert seq.alpha == 0
    assert seq.card_index == len(cards) - 1


def test_skip_card_navigation() -> None:
    """Verifies skip_card jumps cleanly to the next card, and finishes on final card."""
    cards = get_default_cards()
    seq = StartupSequence(cards=cards, gap_seconds=0.15)

    assert seq.card_index == 0
    seq.skip_card()
    assert seq.card_index == 1
    assert seq.is_finished is False

    seq.skip_card()
    assert seq.card_index == 2
    assert seq.is_finished is False

    seq.skip_card()
    assert seq.is_finished is True


def test_skip_all_navigation() -> None:
    """Verifies skip_all immediately finishes the entire sequence."""
    cards = get_default_cards()
    seq = StartupSequence(cards=cards)

    assert seq.is_finished is False
    seq.skip_all()
    assert seq.is_finished is True


def test_broken_or_missing_json_falls_back_to_defaults(tmp_path: Path) -> None:
    """Verifies that non-existent or malformed startup.json gracefully returns default cards."""
    missing_file = tmp_path / "does_not_exist.json"
    cards_missing = load_startup_cards(missing_file)
    assert cards_missing == get_default_cards()

    corrupt_file = tmp_path / "broken.json"
    corrupt_file.write_text("{ not a valid json list [[", encoding="utf-8")
    cards_corrupt = load_startup_cards(corrupt_file)
    assert cards_corrupt == get_default_cards()

    empty_list_file = tmp_path / "empty.json"
    empty_list_file.write_text("[]", encoding="utf-8")
    cards_empty = load_startup_cards(empty_list_file)
    assert cards_empty == get_default_cards()
