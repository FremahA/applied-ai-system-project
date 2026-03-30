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

## Smarter Scheduling

The scheduler goes beyond a simple greedy approach with several features added during implementation:

- **0/1 Knapsack algorithm** — instead of greedily picking tasks by priority until time runs out, the scheduler uses dynamic programming to find the combination of optional tasks with the highest total priority value that fits within the available time.
- **Required tasks** — tasks marked `required=True` are always included in the plan regardless of time pressure, with optional tasks filling whatever time remains.
- **Buffer time** — an owner-level `buffer_minutes` value is inserted between consecutive tasks, giving the owner rest or travel time between activities.
- **Species filtering** — tasks can be restricted to a specific species (`dog`, `cat`, or `other`); ineligible tasks are excluded before scheduling and reported separately in the explanation.
- **Recurring tasks** — tasks with `recurrence="daily"` or `"weekly"` automatically spawn the next occurrence when marked complete, anchored to the original due date to prevent schedule drift.
- **Multi-pet support** — when an owner has multiple pets, available time is allocated proportionally by pending-task count and each pet gets its own plan.
- **Conflict detection** — `Scheduler.detect_conflicts(*plans)` checks all pairs of time slots across multiple pet plans and reports any overlaps.

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
