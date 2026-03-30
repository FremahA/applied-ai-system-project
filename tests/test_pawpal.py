import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, Owner, Scheduler



def test_mark_complete_changes_status_to_complete():
    task = Task(title="Morning walk", duration_minutes=20)
    task.mark_complete()
    assert task.status == "complete"


def test_add_task_increases_task_count_by_one():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Morning walk", duration_minutes=20)
    pet.add_task(task)
    assert len(pet.tasks) == 1


def test_tasks_sorted_by_duration_after_add():
    """Tasks added out of order should be stored shortest-first."""
    pet = Pet(name="Rex", species="dog")
    pet.add_task(Task(title="Long walk", duration_minutes=40))
    pet.add_task(Task(title="Quick brush", duration_minutes=10))
    pet.add_task(Task(title="Play fetch", duration_minutes=25))
    durations = [t.duration_minutes for t in pet.tasks]
    assert durations == sorted(durations)


def test_tasks_sorted_after_each_add():
    """Sort order is maintained incrementally, not just at the end."""
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task(title="A", duration_minutes=30))
    pet.add_task(Task(title="B", duration_minutes=5))
    assert pet.tasks[0].duration_minutes == 5

    pet.add_task(Task(title="C", duration_minutes=15))
    durations = [t.duration_minutes for t in pet.tasks]
    assert durations == sorted(durations)


def test_single_task_list_is_sorted():
    """A list with one task is trivially sorted."""
    pet = Pet(name="Solo", species="other")
    pet.add_task(Task(title="Feed", duration_minutes=10))
    assert len(pet.tasks) == 1


def test_pet_with_no_tasks_is_empty():
    """Edge case: a brand-new pet has an empty task list."""
    pet = Pet(name="Ghost", species="cat")
    assert pet.tasks == []
    assert pet.filter_tasks("pending") == []



def test_daily_recurrence_creates_next_day_task():
    """Completing a daily task spawns a new task due the following day."""
    today = date.today()
    task = Task(title="Feed", duration_minutes=10, recurrence="daily", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.status == "pending"


def test_weekly_recurrence_creates_next_week_task():
    """Completing a weekly task spawns a new task due seven days later."""
    anchor = date(2025, 1, 6)
    task = Task(title="Bath time", duration_minutes=20, recurrence="weekly", due_date=anchor)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == anchor + timedelta(weeks=1)


def test_recurring_task_inherits_all_fields():
    """The spawned task should carry over title, duration, priority, species, required, recurrence."""
    task = Task(
        title="Walk",
        duration_minutes=30,
        priority="high",
        species="dog",
        required=True,
        recurrence="daily",
        due_date=date.today(),
    )
    next_task = task.mark_complete()
    assert next_task.title == task.title
    assert next_task.duration_minutes == task.duration_minutes
    assert next_task.priority == task.priority
    assert next_task.species == task.species
    assert next_task.required == task.required
    assert next_task.recurrence == task.recurrence


def test_non_recurring_task_returns_none():
    """mark_complete on a one-time task returns None (no next occurrence)."""
    task = Task(title="Vet visit", duration_minutes=60)
    result = task.mark_complete()
    assert result is None


def test_recurring_task_no_due_date_uses_today():
    """If due_date is None, the next occurrence is anchored to today."""
    task = Task(title="Feed", duration_minutes=10, recurrence="daily")
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)


def test_complete_task_adds_recurrence_to_pet_and_stays_sorted():
    """Pet.complete_task should append the next occurrence and keep tasks sorted."""
    pet = Pet(name="Rex", species="dog")
    task = Task(title="Walk", duration_minutes=20, recurrence="daily", due_date=date.today())
    pet.add_task(task)
    pet.add_task(Task(title="Brush", duration_minutes=5))
    pet.complete_task(task)
    # original is complete, a new pending walk was added
    pending = pet.filter_tasks("pending")
    durations = [t.duration_minutes for t in pet.tasks]
    assert durations == sorted(durations)
    assert any(t.title == "Walk" and t.status == "pending" for t in pending)



def _make_plan(owner, pet, tasks):
    """Helper: attach tasks to pet and generate a plan."""
    for t in tasks:
        pet.add_task(t)
    return Scheduler(owner, pet).generate_plan()


def test_no_conflict_when_tasks_do_not_overlap():
    """Two plans whose time slots are fully separate should return no conflicts."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Rex", species="dog")
    owner.pets.append(pet)
    plan = _make_plan(
        owner, pet,
        [Task(title="Walk", duration_minutes=20), Task(title="Brush", duration_minutes=10)],
    )
    conflicts = Scheduler.detect_conflicts(plan)
    assert conflicts == []


def test_conflict_flagged_for_overlapping_slots():
    """Two plans that share overlapping time windows should produce a conflict warning."""
    # Build two separate single-task plans that start at minute 0 — they will overlap.
    owner_a = Owner(name="Alex", available_minutes=60)
    pet_a = Pet(name="Rex", species="dog")
    owner_a.pets.append(pet_a)
    pet_a.add_task(Task(title="Walk", duration_minutes=30))
    plan_a = Scheduler(owner_a, pet_a).generate_plan()

    owner_b = Owner(name="Alex", available_minutes=60)
    pet_b = Pet(name="Luna", species="cat")
    owner_b.pets.append(pet_b)
    pet_b.add_task(Task(title="Feed", duration_minutes=20))
    plan_b = Scheduler(owner_b, pet_b).generate_plan()

    conflicts = Scheduler.detect_conflicts(plan_a, plan_b)
    assert len(conflicts) > 0
    assert "WARNING" in conflicts[0]


def test_tasks_touching_at_boundary_are_not_a_conflict():
    """A task that ends exactly when the next begins is NOT a conflict (half-open intervals)."""
    owner = Owner(name="Sam", available_minutes=60)
    pet = Pet(name="Mochi", species="dog")
    owner.pets.append(pet)
    pet.add_task(Task(title="Walk", duration_minutes=20))
    pet.add_task(Task(title="Brush", duration_minutes=10))
    plan = Scheduler(owner, pet).generate_plan()
    # Verify sequential slots don't conflict with themselves
    conflicts = Scheduler.detect_conflicts(plan)
    assert conflicts == []


def test_detect_conflicts_with_no_plans_returns_warning():
    """Calling detect_conflicts with no arguments returns a warning, not an error."""
    result = Scheduler.detect_conflicts()
    assert len(result) == 1
    assert "WARNING" in result[0]


def test_detect_conflicts_with_none_plan_does_not_crash():
    """A None entry in the plan list should be skipped without raising."""
    result = Scheduler.detect_conflicts(None)
    assert isinstance(result, list)


def test_scheduler_with_no_tasks_produces_empty_plan():
    """Edge case: a pet with no tasks yields a plan with zero selected tasks."""
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Ghost", species="cat")
    owner.pets.append(pet)
    plan = Scheduler(owner, pet).generate_plan()
    assert plan.selected_tasks == []
    assert plan.total_minutes_used == 0


def test_required_task_always_included_even_when_over_budget():
    """A required task must appear in the plan even if it exceeds available time."""
    owner = Owner(name="Alex", available_minutes=10)
    pet = Pet(name="Rex", species="dog")
    owner.pets.append(pet)
    pet.add_task(Task(title="Vet", duration_minutes=60, required=True))
    plan = Scheduler(owner, pet).generate_plan()
    assert any(t.title == "Vet" for t in plan.selected_tasks)


def test_species_mismatch_excludes_task_from_plan():
    """A cat-only task should not appear in a dog's plan."""
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Rex", species="dog")
    owner.pets.append(pet)
    pet.add_task(Task(title="Cat grooming", duration_minutes=15, species="cat"))
    plan = Scheduler(owner, pet).generate_plan()
    assert all(t.title != "Cat grooming" for t in plan.selected_tasks)


def test_plan_time_slots_are_sequential():
    """get_time_slots should return non-overlapping, ordered (start, end) pairs."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Rex", species="dog")
    owner.pets.append(pet)
    pet.add_task(Task(title="Walk", duration_minutes=20))
    pet.add_task(Task(title="Brush", duration_minutes=10))
    slots = Scheduler(owner, pet).generate_plan().get_time_slots()
    for i in range(1, len(slots)):
        *_, prev_end = slots[i - 1]
        _, cur_start, _ = slots[i]
        assert cur_start >= prev_end
