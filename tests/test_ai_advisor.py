"""
Reliability tests for the AI Care Agent (ai_advisor.py).

These tests verify the agent's tool implementations directly — no real API
calls are made. They check that the agent correctly identifies care gaps,
adds tasks, prevents duplicates, and produces valid Plans via the Scheduler.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Owner, Pet, Task, Scheduler
from ai_advisor import PawPalAgent, _CARE_CATEGORIES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(minutes=120, buffer=5):
    owner = Owner(name="TestOwner", available_minutes=minutes, buffer_minutes=buffer)
    dog = Pet(name="Rex", species="dog")
    owner.pets.append(dog)
    return PawPalAgent(owner), owner, dog


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------

def test_all_categories_missing_when_no_tasks():
    agent, owner, dog = _make_agent()
    result = agent._analyze_care_gaps("Rex")
    assert set(result["missing_categories"]) == set(_CARE_CATEGORIES.keys())
    assert result["covered_categories"] == []


def test_exercise_covered_by_walk_task():
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Morning walk", duration_minutes=20))
    result = agent._analyze_care_gaps("Rex")
    assert "exercise" not in result["missing_categories"]
    assert "exercise" in result["covered_categories"]


def test_feeding_covered_by_meal_task():
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Morning meal", duration_minutes=5))
    result = agent._analyze_care_gaps("Rex")
    assert "feeding" not in result["missing_categories"]


def test_partial_coverage_reports_remaining_gaps():
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Walk", duration_minutes=20))
    dog.add_task(Task(title="Feed", duration_minutes=5))
    result = agent._analyze_care_gaps("Rex")
    assert "exercise" not in result["missing_categories"]
    assert "feeding" not in result["missing_categories"]
    # grooming, health, enrichment still missing
    assert len(result["missing_categories"]) == 3


def test_unknown_pet_returns_error():
    agent, owner, dog = _make_agent()
    result = agent._analyze_care_gaps("NoSuchPet")
    assert "error" in result


# ---------------------------------------------------------------------------
# add_recommended_task
# ---------------------------------------------------------------------------

def test_add_task_mutates_pet_task_list():
    agent, owner, dog = _make_agent()
    assert len(dog.tasks) == 0
    result = agent._add_recommended_task("Rex", "Brushing session", 10, "medium")
    assert result["status"] == "added"
    assert len(dog.tasks) == 1
    assert dog.tasks[0].title == "Brushing session"


def test_add_task_recorded_in_added_tasks():
    agent, owner, dog = _make_agent()
    agent._add_recommended_task("Rex", "Health check", 5, "medium")
    assert len(agent.added_tasks) == 1
    assert agent.added_tasks[0]["title"] == "Health check"
    assert agent.added_tasks[0]["pet"] == "Rex"


def test_duplicate_task_is_skipped():
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Morning walk", duration_minutes=20))
    result = agent._add_recommended_task("Rex", "Morning walk", 20, "high")
    assert result["status"] == "skipped"
    assert len(dog.tasks) == 1  # no duplicate added
    assert len(agent.added_tasks) == 0


def test_duplicate_check_is_case_insensitive():
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Morning Walk", duration_minutes=20))
    result = agent._add_recommended_task("Rex", "morning walk", 20, "high")
    assert result["status"] == "skipped"


def test_add_task_to_unknown_pet_returns_error():
    agent, owner, dog = _make_agent()
    result = agent._add_recommended_task("Ghost", "Walk", 20, "medium")
    assert "error" in result
    assert len(dog.tasks) == 0


def test_required_flag_is_passed_through():
    agent, owner, dog = _make_agent()
    agent._add_recommended_task("Rex", "Morning feeding", 5, "high", required=True)
    assert dog.tasks[0].required is True


# ---------------------------------------------------------------------------
# generate_optimized_schedule
# ---------------------------------------------------------------------------

def test_generate_schedule_returns_plan_object():
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Walk", duration_minutes=20))
    result = agent._generate_optimized_schedule("Rex")
    assert "tasks_scheduled" in result
    assert "total_minutes_used" in result
    assert result["tasks_scheduled"] == 1


def test_generated_plan_stored_in_agent():
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Walk", duration_minutes=20))
    agent._generate_optimized_schedule("Rex")
    assert "Rex" in agent.generated_plans


def test_schedule_reflects_ai_added_tasks():
    """Tasks added by the agent must appear in the generated schedule."""
    agent, owner, dog = _make_agent()
    dog.add_task(Task(title="Walk", duration_minutes=20))
    agent._add_recommended_task("Rex", "Brushing session", 10, "medium")
    result = agent._generate_optimized_schedule("Rex")
    scheduled_titles = {s["task"] for s in result["schedule"]}
    assert "Walk" in scheduled_titles
    assert "Brushing session" in scheduled_titles


def test_schedule_for_unknown_pet_returns_error():
    agent, owner, dog = _make_agent()
    result = agent._generate_optimized_schedule("Ghost")
    assert "error" in result


def test_schedule_respects_time_budget():
    """Total minutes used must not exceed available_minutes."""
    agent, owner, dog = _make_agent(minutes=30)
    for title, dur in [("Walk", 20), ("Brush", 10), ("Play", 15), ("Train", 20)]:
        dog.add_task(Task(title=title, duration_minutes=dur))
    result = agent._generate_optimized_schedule("Rex")
    assert result["total_minutes_used"] <= 30


# ---------------------------------------------------------------------------
# get_pets_and_tasks
# ---------------------------------------------------------------------------

def test_get_pets_and_tasks_returns_all_pets():
    owner = Owner(name="Sam", available_minutes=90)
    dog = Pet(name="Rex", species="dog")
    cat = Pet(name="Luna", species="cat")
    owner.pets += [dog, cat]
    dog.add_task(Task(title="Walk", duration_minutes=20))
    agent = PawPalAgent(owner)
    state = agent._get_pets_and_tasks()
    assert "Rex" in state and "Luna" in state
    assert len(state["Rex"]["pending_tasks"]) == 1
    assert len(state["Luna"]["pending_tasks"]) == 0


def test_completed_tasks_excluded_from_state():
    agent, owner, dog = _make_agent()
    t = Task(title="Walk", duration_minutes=20)
    dog.add_task(t)
    t.status = "complete"
    state = agent._get_pets_and_tasks()
    assert len(state["Rex"]["pending_tasks"]) == 0
