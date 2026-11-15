# Written with Claude in Antigravity. Reviewed by LunArk team.
"""Unit tests for Stage 8 TutorialManager logic (pure-Python, no pygame)."""

from game.logic.tutorial import TutorialManager
from game.logic.state import GameState


def test_initial_state():
    """Tutorial starts at step 0 (welcome/name) and is active."""
    tm = TutorialManager()
    assert tm.step_index == 0
    assert tm.is_active is True
    assert tm.is_completed is False
    assert tm.player_name == "Commander"


def test_set_player_name_valid():
    """set_player_name stores trimmed name, clamped to max_name_length."""
    tm = TutorialManager()
    tm.set_player_name("  Zara  ")
    assert tm.player_name == "Zara"

    tm.set_player_name("A" * 20)  # over max (12)
    assert len(tm.player_name) == tm.max_name_length


def test_set_player_name_empty_fallback():
    """Empty name falls back to 'Commander'."""
    tm = TutorialManager()
    tm.set_player_name("   ")
    assert tm.player_name == "Commander"


def test_advance_through_all_steps():
    """advance_step moves step_index from 0 to 7 (completion) then 8 (done)."""
    tm = TutorialManager()
    # Steps 0 → 7
    for expected in range(1, 8):
        tm.advance_step()
        assert tm.step_index == expected

    # At step 7, badge is awarded
    assert tm.badge_awarded is not None
    assert tm.is_active is True  # still showing completion slide

    # One more advance → done
    tm.advance_step()
    assert tm.step_index == 8
    assert tm.is_active is False
    assert tm.is_completed is True


def test_skip_immediately_completes():
    """skip() deactivates tutorial without stepping through."""
    tm = TutorialManager()
    tm.skip()
    assert tm.is_active is False
    assert tm.is_completed is True
    assert tm.is_skipped is True


def test_restart_tutorial():
    """restart_tutorial() brings the player back to step 1 and reactivates."""
    tm = TutorialManager()
    tm.skip()
    tm.restart_tutorial()
    assert tm.step_index == 1
    assert tm.is_active is True
    assert tm.is_completed is False


def test_get_current_info_welcome():
    """Step 0 returns welcome info with name_input target."""
    tm = TutorialManager()
    info = tm.get_current_info()
    assert info["step"] == 0
    assert info["active"] is True
    assert info["target"] == "name_input"
    assert isinstance(info["dialogue"], list)
    assert len(info["dialogue"]) > 0


def test_get_current_info_steps():
    """Steps 1-6 return valid step data with title and dialogue."""
    tm = TutorialManager()
    for s in range(1, 7):
        tm.step_index = s
        info = tm.get_current_info()
        assert info["step"] == s
        assert info["active"] is True
        assert isinstance(info["title"], str) and len(info["title"]) > 0
        assert isinstance(info["dialogue"], list) and len(info["dialogue"]) > 0


def test_get_current_info_completion():
    """Step 7 returns completion info with badge target."""
    tm = TutorialManager()
    tm.step_index = 7
    tm.badge_awarded = "LunArk Cadet Wings"
    info = tm.get_current_info()
    assert info["step"] == 7
    assert info["target"] == "badge"
    assert isinstance(info["dialogue"], list)


def test_inactive_returns_empty():
    """Inactive tutorial returns active=False with empty dialogue."""
    tm = TutorialManager()
    tm.skip()
    info = tm.get_current_info()
    assert info["active"] is False
    assert info["dialogue"] == []


def test_training_constraints_clamp_indicators():
    """enforce_training_constraints clamps energy, boredom, and revenue."""
    tm = TutorialManager()
    state = GameState()

    # Push to extremes
    state.energy = 0.0
    state.boredom = 100.0
    state.revenue = 0.0

    tm.enforce_training_constraints(state)

    assert state.energy >= 25.0
    assert state.boredom <= 50.0
    assert state.revenue >= 50.0


def test_training_constraints_inactive():
    """Skipped tutorial does NOT clamp indicators."""
    tm = TutorialManager()
    tm.skip()
    state = GameState()
    state.energy = 0.0
    state.boredom = 100.0
    state.revenue = 0.0

    tm.enforce_training_constraints(state)

    # Unchanged because tutorial is inactive
    assert state.energy == 0.0
    assert state.boredom == 100.0
    assert state.revenue == 0.0


def test_glossary_has_entries():
    """Glossary returns a list of dicts with 'term' and 'definition' fields."""
    tm = TutorialManager()
    glossary = tm.get_glossary()
    assert isinstance(glossary, list)
    assert len(glossary) > 0
    for entry in glossary:
        assert "term" in entry
        assert "definition" in entry
        assert isinstance(entry["term"], str)
        assert isinstance(entry["definition"], str)
