"""
PawPal+ system classes.
"""

from dataclasses import dataclass
from typing import Optional

VALID_PRIORITIES = {"high", "medium", "low"}
VALID_SPECIES = {"dog", "cat", "other"}


@dataclass
class Owner:
    """Represents the pet owner and their scheduling constraints."""
    name: str
    available_minutes: int  # total time available today

    def __post_init__(self):
        if self.available_minutes <= 0:
            raise ValueError(f"available_minutes must be positive, got {self.available_minutes}")


@dataclass
class Pet:
    """Represents the pet being cared for."""
    name: str
    species: str  # "dog", "cat", or "other"

    def __post_init__(self):
        if self.species not in VALID_SPECIES:
            raise ValueError(f"species must be one of {VALID_SPECIES}, got '{self.species}'")


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration_minutes: int
    priority: str = "medium"  # "high", "medium", or "low"
    species: Optional[str] = None  # if set, task only applies to this species

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.species is not None and self.species not in VALID_SPECIES:
            raise ValueError(f"species must be one of {VALID_SPECIES}, got '{self.species}'")

    @property
    def priority_value(self) -> int:
        return {"high": 3, "medium": 2, "low": 1}[self.priority]


@dataclass
class Plan:
    """Represents the final daily schedule produced by the Scheduler."""
    owner: Owner
    pet: Pet
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
        """Build a daily plan using 0/1 knapsack to maximise priority within available time."""
        eligible = [t for t in self.tasks if t.species is None or t.species == self.pet.species]
        ineligible = [t for t in self.tasks if t.species is not None and t.species != self.pet.species]

        selected = self._knapsack_select(eligible)
        selected_ids = {id(t) for t in selected}
        skipped = [t for t in eligible if id(t) not in selected_ids]

        time_used = sum(t.duration_minutes for t in selected)
        explanation = self._build_explanation(selected, skipped, ineligible, time_used)
        return Plan(
            owner=self.owner,
            pet=self.pet,
            selected_tasks=selected,
            total_minutes_used=time_used,
            explanation=explanation,
        )

    def _knapsack_select(self, tasks: list[Task]) -> list[Task]:
        """0/1 knapsack DP: maximise total priority value within available_minutes."""
        capacity = self.owner.available_minutes
        n = len(tasks)
        # dp[i][c] = best priority value using the first i tasks with c minutes remaining
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]

        for i, task in enumerate(tasks, 1):
            w = task.duration_minutes
            v = task.priority_value
            for c in range(capacity + 1):
                if w > c:
                    dp[i][c] = dp[i - 1][c]
                else:
                    dp[i][c] = max(dp[i - 1][c], dp[i - 1][c - w] + v)

        # Backtrack to recover selected tasks
        selected = []
        c = capacity
        for i in range(n, 0, -1):
            if dp[i][c] != dp[i - 1][c]:
                selected.append(tasks[i - 1])
                c -= tasks[i - 1].duration_minutes

        return sorted(selected, key=lambda t: (-t.priority_value, t.duration_minutes))

    def _build_explanation(
        self,
        selected: list[Task],
        skipped: list[Task],
        ineligible: list[Task],
        time_used: int,
    ) -> str:
        lines = [
            f"Plan for {self.pet.name} ({self.pet.species}) — "
            f"{self.owner.name} has {self.owner.available_minutes} min available.",
            f"Selected {len(selected)} task(s) using {time_used} min:",
        ]
        for task in selected:
            lines.append(f"  • {task.title} ({task.priority} priority, {task.duration_minutes} min)")
        if skipped:
            lines.append(f"Skipped {len(skipped)} task(s) due to time constraints:")
            for task in skipped:
                lines.append(f"  • {task.title} ({task.priority} priority, {task.duration_minutes} min)")
        if ineligible:
            lines.append(f"Excluded {len(ineligible)} task(s) not applicable to {self.pet.species}s:")
            for task in ineligible:
                lines.append(f"  • {task.title} (for {task.species}s)")
        return "\n".join(lines)


class StreamlitUI:
    """Thin wrapper that connects the system classes to the Streamlit frontend."""

    def __init__(self):
        self.owner: Optional[Owner] = None
        self.pet: Optional[Pet] = None
        self.tasks: list[Task] = []
        self.plan: Optional[Plan] = None

    def build_and_run_scheduler(self) -> Optional[Plan]:
        """Create a Scheduler from current state, store and return the generated Plan."""
        if self.owner is None or self.pet is None:
            return None
        scheduler = Scheduler(owner=self.owner, pet=self.pet, tasks=self.tasks)
        self.plan = scheduler.generate_plan()
        return self.plan
