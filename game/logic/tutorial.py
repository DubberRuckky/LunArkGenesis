# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python tutorial and onboarding logic for LunArk: Genesis.

Strictly NO pygame imports.
Manages:
- 6-step guided walkthrough with Lieutenant Vance
- Commander callsign/name prompt (max 12 characters)
- Safe training mode constraints (blocks events, natural boredom rise, indicator limits)
- Step transitions, skipping, completion badge, and science glossary access
"""

from typing import Any

from game.logic.data import load_tutorial
from game.logic.state import GameState


class TutorialManager:
    """Manages guided tutorial progress, dialogues, training constraints, and glossary."""

    def __init__(self, tutorial_data: dict[str, Any] | None = None) -> None:
        self.data: dict[str, Any] = tutorial_data or load_tutorial()

        # Player identity
        welcome_cfg = self.data.get("welcome", {})
        self.player_name: str = welcome_cfg.get("default_name", "Commander")
        self.max_name_length: int = int(welcome_cfg.get("max_name_length", 12))

        # Progression:
        # 0 = Welcome / Name input
        # 1..6 = Steps 1 to 6
        # 7 = Completion / Badge
        # 8 = Done / Inactive
        self.step_index: int = 0
        self.is_active: bool = True
        self.is_completed: bool = False
        self.is_skipped: bool = False
        self.badge_awarded: str | None = None

        self.steps: list[dict[str, Any]] = self.data.get("steps", [])

    def set_player_name(self, name: str) -> None:
        """Set the player's Commander name with length clamping and fallback."""
        clean_name = name.strip()[:self.max_name_length]
        if not clean_name:
            clean_name = "Commander"
        self.player_name = clean_name

    def advance_step(self) -> None:
        """Advance to the next tutorial step or complete."""
        if not self.is_active:
            return

        self.step_index += 1
        if self.step_index == 7:
            # Reached completion
            comp_cfg = self.data.get("completion", {})
            self.badge_awarded = comp_cfg.get("badge_title", "LunArk Cadet Wings")
        elif self.step_index >= 8:
            # Tutorial complete
            self.is_active = False
            self.is_completed = True

    def skip(self) -> None:
        """Immediately skip the tutorial and enable full simulation."""
        self.is_active = False
        self.is_completed = True
        self.is_skipped = True
        self.step_index = 8

    def restart_tutorial(self) -> None:
        """Restart the tutorial from step 1 for replay."""
        self.step_index = 1
        self.is_active = True
        self.is_completed = False
        self.is_skipped = False

    def get_current_info(self) -> dict[str, Any]:
        """Return information for rendering the current tutorial dialogue box."""
        if not self.is_active:
            return {
                "active": False,
                "step": self.step_index,
                "title": "",
                "dialogue": [],
                "expression": 0,
                "target": None,
            }

        if self.step_index == 0:
            w_cfg = self.data.get("welcome", {})
            return {
                "active": True,
                "step": 0,
                "title": "Welcome to LunArk",
                "dialogue": w_cfg.get("dialogue", []),
                "expression": w_cfg.get("expression", 1),
                "target": "name_input",
            }

        if 1 <= self.step_index <= len(self.steps):
            step_cfg = self.steps[self.step_index - 1]
            return {
                "active": True,
                "step": self.step_index,
                "title": step_cfg.get("title", f"Step {self.step_index}"),
                "dialogue": step_cfg.get("dialogue", []),
                "expression": step_cfg.get("expression", 0),
                "target": step_cfg.get("target"),
                "category": step_cfg.get("category"),
                "building_id": step_cfg.get("building_id"),
                "camera_col": step_cfg.get("camera_col"),
            }

        if self.step_index == 7:
            comp_cfg = self.data.get("completion", {})
            return {
                "active": True,
                "step": 7,
                "title": comp_cfg.get("badge_title", "Cadet Wings Awarded"),
                "dialogue": comp_cfg.get("dialogue", []),
                "expression": comp_cfg.get("expression", 3),
                "target": "badge",
            }

        return {
            "active": False,
            "step": self.step_index,
            "title": "",
            "dialogue": [],
            "expression": 0,
            "target": None,
        }

    def enforce_training_constraints(self, state: GameState) -> None:
        """Clamp indicators during tutorial so base cannot fail while learning."""
        if not self.is_active:
            return

        # Keep energy safely between 25 and 100
        state.energy = max(25.0, min(100.0, state.energy))
        # Keep boredom safely between 0 and 50
        state.boredom = max(0.0, min(50.0, state.boredom))
        # Keep revenue above 50 so player can afford tutorial buildings
        state.revenue = max(50.0, state.revenue)

    def get_glossary(self) -> list[dict[str, Any]]:
        """Return the science glossary entries."""
        return self.data.get("glossary", [])
