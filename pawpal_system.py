"""
PawPal+ system classes.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Owner:
    """Represents the pet owner and their scheduling constraints."""
    name: str
    available_minutes: int  # total time available today


@dataclass
class Pet:
    """Represents the pet being cared for."""
    name: str
    species: str  # e.g. "dog", "cat", "other"


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration_minutes: int
    priority: str = "medium"  # "high", "medium", or "low"

    PRIORITY_ORDER: dict = field(default_factory=lambda: {"high": 3, "medium": 2, "low": 1}, repr=False, compare=False)

    @property
    def priority_value(self) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 0)


@dataclass
class Plan:
    """Represents the final daily schedule produced by the Scheduler."""
    selected_tasks: list[Task]
    total_minutes_used: int
    explanation: str


class Scheduler:
    """Selects and orders tasks to fit within the owner's available time."""

    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def generate_plan(self) -> Plan:
        """Build a daily plan by selecting tasks that fit within available time."""
        # Sort by priority (highest first), then by duration (shortest first)
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (-t.priority_value, t.duration_minutes),
        )

        selected = []
        time_used = 0
        skipped = []

        for task in sorted_tasks:
            if time_used + task.duration_minutes <= self.owner.available_minutes:
                selected.append(task)
                time_used += task.duration_minutes
            else:
                skipped.append(task)

        explanation = self._build_explanation(selected, skipped, time_used)
        return Plan(selected_tasks=selected, total_minutes_used=time_used, explanation=explanation)

    def _build_explanation(
        self, selected: list[Task], skipped: list[Task], time_used: int
    ) -> str:
        lines = [
            f"Plan for {self.pet.name} — {self.owner.name} has {self.owner.available_minutes} min available.",
            f"Selected {len(selected)} task(s) using {time_used} min:",
        ]
        for task in selected:
            lines.append(f"  • {task.title} ({task.priority} priority, {task.duration_minutes} min)")
        if skipped:
            lines.append(f"Skipped {len(skipped)} task(s) due to time constraints:")
            for task in skipped:
                lines.append(f"  • {task.title} ({task.priority} priority, {task.duration_minutes} min)")
        return "\n".join(lines)


class StreamlitUI:
    """Thin wrapper that connects the system classes to the Streamlit frontend."""

    def __init__(self):
        self.owner: Optional[Owner] = None
        self.pet: Optional[Pet] = None
        self.tasks: list[Task] = []

    def build_and_run_scheduler(self) -> Optional[Plan]:
        """Create a Scheduler from current state and return the generated Plan."""
        if self.owner is None or self.pet is None:
            return None
        scheduler = Scheduler(owner=self.owner, pet=self.pet, tasks=self.tasks)
        return scheduler.generate_plan()
