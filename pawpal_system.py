"""
PawPal+ system classes.

Architecture overview
---------------------
The system is built around five classes that form a clean pipeline from input
to scheduled output:

    Owner ──owns──► Pet ──has──► Task
                               │
                    Scheduler ─┘
                        │
                        ▼
                      Plan

Owner
    Stores the pet owner's name, total daily time budget (available_minutes),
    and optional buffer time to insert between tasks (buffer_minutes).  When
    an owner has multiple pets the Scheduler allocates time proportionally
    across them based on pending-task count.

Pet
    Stores a pet's name and species ("dog", "cat", or "other") and maintains
    its ordered task list.  Tasks are kept sorted by duration after every
    add_task or complete_task call.

Task
    A single care activity with a title, duration, priority, and optional
    metadata:
      - species     : restricts the task to a specific species (default: any).
      - required    : if True, the task is always scheduled regardless of time.
      - recurrence  : "daily" or "weekly"; completing a recurring task
                      automatically spawns the next occurrence.
      - due_date    : anchor date for the next occurrence of a recurring task.

Scheduler
    Produces a Plan for a given (Owner, Pet) pair.  The algorithm:
      1. Filter tasks by species eligibility.
      2. Always include required tasks.
      3. Fill remaining time with optional tasks via 0/1 knapsack DP,
         maximising total priority value.
      4. Detect cross-plan time-slot conflicts (static helper).

Plan
    Immutable record of the scheduled tasks, total minutes used, and a
    human-readable explanation.  get_time_slots() returns (task, start, end)
    tuples laid out sequentially with buffer gaps.

StreamlitUI
    Thin glue layer that holds the current Owner, Pet, and Plan in one place
    and delegates scheduling to Scheduler.  Used by app.py.

Quick-start example
-------------------
    from pawpal_system import Owner, Pet, Task, Scheduler

    owner = Owner(name="Alex", available_minutes=60, buffer_minutes=5)
    dog   = Pet(name="Rex", species="dog")
    owner.pets.append(dog)

    dog.add_task(Task(title="Morning walk",  duration_minutes=20, priority="high"))
    dog.add_task(Task(title="Brushing",      duration_minutes=10, priority="medium"))
    dog.add_task(Task(title="Play fetch",    duration_minutes=30, priority="low"))

    plan = Scheduler(owner, dog).generate_plan()
    print(plan.explanation)

Constants
---------
VALID_PRIORITIES   : {"high", "medium", "low"}
VALID_SPECIES      : {"dog", "cat", "other"}
VALID_RECURRENCES  : {"daily", "weekly"}
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

VALID_PRIORITIES = {"high", "medium", "low"}
VALID_SPECIES = {"dog", "cat", "other"}
VALID_RECURRENCES = {"daily", "weekly"}


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

    def complete_task(self, task: "Task") -> None:
        """Mark a task complete and auto-add the next occurrence if it recurs."""
        next_occurrence = task.mark_complete()
        if next_occurrence is not None:
            self.add_task(next_occurrence)

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
    recurrence: Optional[str] = None  # "daily", "weekly", or None for one-time tasks
    due_date: Optional[date] = None  # next scheduled date for recurring tasks

    def __post_init__(self):
        """Validate priority, duration_minutes, species, and recurrence."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.species is not None and self.species not in VALID_SPECIES:
            raise ValueError(f"species must be one of {VALID_SPECIES}, got '{self.species}'")
        if self.recurrence is not None and self.recurrence not in VALID_RECURRENCES:
            raise ValueError(f"recurrence must be one of {VALID_RECURRENCES} or None, got '{self.recurrence}'")

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as complete and return a new pending instance if recurring.

        The next due_date is calculated from the current due_date (or today if unset):
          - "daily"  → current date + timedelta(days=1)
          - "weekly" → current date + timedelta(weeks=1)
        Using the existing due_date as the base prevents drift when catching up on
        missed tasks — each occurrence stays anchored to the original schedule.
        """
        self.status = "complete"
        if self.recurrence in VALID_RECURRENCES:
            base = self.due_date if self.due_date is not None else date.today()
            delta = timedelta(days=1) if self.recurrence == "daily" else timedelta(weeks=1)
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                species=self.species,
                required=self.required,
                recurrence=self.recurrence,
                due_date=base + delta,
            )
        return None

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

    def get_time_slots(self) -> list[tuple[Task, int, int]]:
        """Return (task, start_min, end_min) for each selected task, in schedule order.

        Tasks are laid out sequentially starting at minute 0, with
        owner.buffer_minutes inserted between consecutive tasks.
        """
        slots: list[tuple[Task, int, int]] = []
        buf = self.owner.buffer_minutes
        current = 0
        for task in self.selected_tasks:
            end = current + task.duration_minutes
            slots.append((task, current, end))
            current = end + buf
        return slots


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

    @staticmethod
    def detect_conflicts(*plans: "Plan") -> list[str]:
        """Check all pairs of time slots across the given plans for overlaps.

        Lightweight strategy: every failure path returns a warning string instead
        of raising. The caller always receives a plain list[str] — conflict messages
        mixed with any WARNING lines — and the program never crashes.

        Two tasks conflict when their intervals overlap: a task that ends exactly
        when another begins is NOT a conflict (intervals are half-open [start, end)).
        """
        if not plans:
            return ["WARNING: no plans provided — nothing to check."]

        # Build a flat list of (pet_name, task, start, end), skipping bad entries
        entries: list[tuple[str, Task, int, int]] = []
        for plan in plans:
            if plan is None:
                entries  # skip silently — warning below
                continue
            try:
                pet_name = plan.pet.name if plan.pet is not None else "unknown pet"
                for task, start, end in plan.get_time_slots():
                    entries.append((pet_name, task, start, end))
            except Exception as exc:  # noqa: BLE001
                return [f"WARNING: could not read time slots — {exc}"]

        if not entries:
            return ["WARNING: all plans were empty — no tasks to compare."]

        conflicts: list[str] = []
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                pet_a, task_a, start_a, end_a = entries[i]
                pet_b, task_b, start_b, end_b = entries[j]
                if start_a < end_b and start_b < end_a:
                    conflicts.append(
                        f"WARNING: [{start_a}–{end_a} min] '{task_a.title}' ({pet_a})"
                        f" overlaps [{start_b}–{end_b} min] '{task_b.title}' ({pet_b})"
                    )
        return conflicts

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
