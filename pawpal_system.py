"""
PawPal+ system classes.
"""

from dataclasses import dataclass, field
from typing import Optional

VALID_PRIORITIES = {"high", "medium", "low"}
VALID_SPECIES = {"dog", "cat", "other"}


@dataclass
class Owner:
    """Represents the pet owner and their scheduling constraints."""
    name: str
    available_minutes: int  # total time available today
    buffer_minutes: int = 0  # rest/travel time to insert between tasks
    pets: list["Pet"] = field(default_factory=list)

    def __post_init__(self):
        """Validate that available_minutes is positive and buffer_minutes is non-negative."""
        if self.available_minutes <= 0:
            raise ValueError(f"available_minutes must be positive, got {self.available_minutes}")
        if self.buffer_minutes < 0:
            raise ValueError(f"buffer_minutes must be non-negative, got {self.buffer_minutes}")

    def get_tasks_by_pet(self, pet_name: str) -> list["Task"]:
        """Return all tasks for the pet with the given name, or [] if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.tasks
        return []


@dataclass
class Pet:
    """Represents the pet being cared for."""
    name: str
    species: str  # "dog", "cat", or "other"
    tasks: list["Task"] = field(default_factory=list)

    def __post_init__(self):
        """Validate that species is one of the allowed values."""
        if self.species not in VALID_SPECIES:
            raise ValueError(f"species must be one of {VALID_SPECIES}, got '{self.species}'")

    def add_task(self, task: "Task") -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)
        self.tasks.sort(key=lambda t: t.duration_minutes)

    def filter_tasks(self, status: str) -> list["Task"]:
        """Return tasks matching the given status ('pending' or 'complete')."""
        return [t for t in self.tasks if t.status == status]


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration_minutes: int
    priority: str = "medium"  # "high", "medium", or "low"
    species: Optional[str] = None  # if set, task only applies to this species
    status: str = "pending"  # "pending" or "complete"
    required: bool = False  # if True, always included regardless of time pressure

    def __post_init__(self):
        """Validate priority, duration_minutes, and species."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.species is not None and self.species not in VALID_SPECIES:
            raise ValueError(f"species must be one of {VALID_SPECIES}, got '{self.species}'")

    def mark_complete(self) -> None:
        """Mark this task as complete."""
        self.status = "complete"

    @property
    def priority_value(self) -> int:
        """Return a numeric weight for the priority: high=3, medium=2, low=1."""
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

    def __init__(self, owner: Owner, pet: Pet):
        """Store the owner and pet, and alias the pet's task list."""
        self.owner = owner
        self.pet = pet
        self.tasks = self.pet.tasks

    def generate_plan(self) -> Plan:
        """Build a daily plan: required tasks are always included; optional tasks fill remaining time via knapsack."""
        eligible = [t for t in self.tasks if t.species is None or t.species == self.pet.species]
        ineligible = [t for t in self.tasks if t.species is not None and t.species != self.pet.species]

        required = [t for t in eligible if t.required]
        optional = [t for t in eligible if not t.required]

        buf = self.owner.buffer_minutes
        capacity = self._compute_pet_capacity()

        # Reserve time for required tasks (duration + buffer slot after each)
        required_cost = sum(t.duration_minutes + buf for t in required)
        remaining = capacity - required_cost

        if remaining < 0:
            # Required tasks alone exceed capacity — include them all, skip optional
            selected_optional: list[Task] = []
            skipped = optional
        else:
            selected_optional = self._knapsack_select(optional, remaining)
            selected_ids = {id(t) for t in selected_optional}
            skipped = [t for t in optional if id(t) not in selected_ids]

        # Required tasks first, then optional sorted by priority then duration
        selected = required + sorted(selected_optional, key=lambda t: (-t.priority_value, t.duration_minutes))

        time_used = sum(t.duration_minutes for t in selected)
        if len(selected) > 1:
            time_used += buf * (len(selected) - 1)

        explanation = self._build_explanation(selected, skipped, ineligible, time_used)
        return Plan(
            owner=self.owner,
            pet=self.pet,
            selected_tasks=selected,
            total_minutes_used=time_used,
            explanation=explanation,
        )

    def _compute_pet_capacity(self) -> int:
        """Allocate available_minutes proportionally across owner's pets by pending-task count."""
        pets = self.owner.pets
        if len(pets) <= 1:
            return self.owner.available_minutes
        total_tasks = sum(len(p.tasks) for p in pets)
        if total_tasks == 0:
            return self.owner.available_minutes // len(pets)
        share = len(self.pet.tasks) / total_tasks
        return max(1, int(self.owner.available_minutes * share))

    def _knapsack_select(self, tasks: list[Task], capacity: int) -> list[Task]:
        """0/1 knapsack DP: maximise total priority within capacity.

        Pre-sorts tasks so higher-priority, shorter tasks land at higher indices.
        Backtracking (n→1) then naturally picks them first on ties (#1).
        Each task's DP weight includes a buffer slot after it (#8).
        """
        # Low-priority long tasks first → high-priority short tasks last (higher index)
        tasks = sorted(tasks, key=lambda t: (t.priority_value, -t.duration_minutes))

        buf = self.owner.buffer_minutes
        n = len(tasks)
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]

        for i, task in enumerate(tasks, 1):
            w = task.duration_minutes + buf  # duration + buffer after this task
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
                c -= tasks[i - 1].duration_minutes + buf

        return selected

    def _build_explanation(
        self,
        selected: list[Task],
        skipped: list[Task],
        ineligible: list[Task],
        time_used: int,
    ) -> str:
        """Build a human-readable summary of selected, skipped, and excluded tasks."""
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
        """Initialize with no owner, pet, or plan set."""
        self.owner: Optional[Owner] = None
        self.pet: Optional[Pet] = None
        self.plan: Optional[Plan] = None

    def build_and_run_scheduler(self) -> Optional[Plan]:
        """Create a Scheduler from current state, store and return the generated Plan."""
        if self.owner is None or self.pet is None:
            return None
        scheduler = Scheduler(owner=self.owner, pet=self.pet)
        self.plan = scheduler.generate_plan()
        return self.plan
