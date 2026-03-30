# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- **Sorting by duration** — tasks are kept sorted shortest-first after every add or completion, so the task list is always in a predictable order.
- **Priority-based ordering** — selected optional tasks are placed into the plan from highest to lowest priority, with shortest duration breaking ties.
- **0/1 Knapsack optimization** — the scheduler uses bottom-up dynamic programming to find the combination of optional tasks with the highest total priority value that fits within the available time.
- **Required task guarantee** — tasks marked required are always included in the plan regardless of time pressure; optional tasks fill whatever capacity remains.
- **Buffer time between tasks** — an owner-level buffer is inserted between consecutive tasks and counted against capacity during scheduling.
- **Species filtering** — tasks can be restricted to a specific species; ineligible tasks are excluded before scheduling and reported separately in the plan explanation.
- **Daily and weekly recurrence** — completing a recurring task automatically spawns the next occurrence anchored to the original due date to prevent schedule drift.
- **Proportional multi-pet time allocation** — when an owner has multiple pets, available minutes are split proportionally by each pet's pending-task count.
- **Sequential time-slot layout** — the plan produces start and end times for each task laid out from minute 0 with buffer gaps, used by both the UI and conflict detection.
- **Cross-plan conflict detection** — checks all pairs of time slots across multiple pet plans for overlaps and returns human-readable warnings instead of crashing on bad input.

## Smarter Scheduling

The scheduler goes beyond a simple greedy approach. Rather than picking tasks by priority until time runs out, it uses a 0/1 knapsack algorithm to find the highest-value combination of tasks that fits the available time. Required tasks are always guaranteed a spot, and whatever time remains is offered to optional tasks. When an owner has multiple pets, time is divided proportionally so no pet is shortchanged. The system also handles recurring tasks, species restrictions, buffer gaps between activities, and can detect scheduling conflicts across multiple pet plans.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The suite contains 21 tests organized into four areas:

| Area | What is tested |
|---|---|
| **Sorting** | Tasks added in any order are stored shortest-first; sort is maintained after every `add_task` call; an empty pet list is handled correctly. |
| **Recurrence** | Completing a `daily` task spawns a new task due the next day; `weekly` advances by 7 days; the spawned task inherits all fields and starts as `pending`; a missing `due_date` falls back to today. |
| **Conflict detection** | Non-overlapping plans produce no warnings; overlapping time slots are flagged; tasks that touch at a boundary (end == start) are correctly treated as non-conflicting; edge inputs (`None`, no plans) return warning strings instead of crashing. |
| **Scheduler** | A pet with no tasks yields an empty plan; required tasks are always included even when they exceed the time budget; species-mismatched tasks are excluded; generated time slots are strictly sequential. |

### Confidence Level

**4 / 5 stars**

