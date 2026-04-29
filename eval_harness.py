"""
PawPal+ AI Agent Evaluation Harness

Runs the AI Care Agent's tool layer on predefined scenarios and prints a
pass/fail report with scores. No API key required — evaluates the deterministic
tool implementations that the agent uses, which is where correctness matters most.

Usage:
    python eval_harness.py
"""

from pawpal_system import Owner, Pet, Task
from ai_advisor import PawPalAgent, _CARE_CATEGORIES

# ── Scenarios ──────────────────────────────────────────────────────────────
# Each scenario defines a starting state and the expected behavior.

SCENARIOS = [
    {
        "id": 1,
        "name": "Dog with no tasks — all 5 gaps expected",
        "owner_minutes": 120,
        "buffer": 5,
        "pets": [{"name": "Rex", "species": "dog", "tasks": []}],
        "checks": {
            "gap_categories": {"Rex": set(_CARE_CATEGORIES.keys())},
        },
    },
    {
        "id": 2,
        "name": "Cat with feeding only — 4 gaps expected",
        "owner_minutes": 90,
        "buffer": 5,
        "pets": [{"name": "Luna", "species": "cat", "tasks": [
            {"title": "Morning feeding", "duration": 5, "priority": "high"},
        ]}],
        "checks": {
            "gap_categories": {"Luna": {"exercise", "grooming", "health", "enrichment"}},
        },
    },
    {
        "id": 3,
        "name": "Dog with exercise + feeding — 3 gaps expected",
        "owner_minutes": 90,
        "buffer": 5,
        "pets": [{"name": "Buddy", "species": "dog", "tasks": [
            {"title": "Morning walk", "duration": 20, "priority": "high"},
            {"title": "Afternoon meal", "duration": 10, "priority": "high"},
        ]}],
        "checks": {
            "gap_categories": {"Buddy": {"grooming", "health", "enrichment"}},
        },
    },
    {
        "id": 4,
        "name": "Fully covered pet — 0 gaps expected",
        "owner_minutes": 120,
        "buffer": 5,
        "pets": [{"name": "Max", "species": "dog", "tasks": [
            {"title": "Morning walk",      "duration": 20, "priority": "high"},
            {"title": "Morning feeding",   "duration": 5,  "priority": "high"},
            {"title": "Brushing session",  "duration": 10, "priority": "medium"},
            {"title": "Health check",      "duration": 5,  "priority": "medium"},
            {"title": "Training session",  "duration": 15, "priority": "medium"},
        ]}],
        "checks": {
            "gap_categories": {"Max": set()},
        },
    },
    {
        "id": 5,
        "name": "Tight budget — schedule must not exceed available minutes",
        "owner_minutes": 25,
        "buffer": 0,
        "pets": [{"name": "Pip", "species": "cat", "tasks": [
            {"title": "Morning feeding", "duration": 5, "priority": "high"},
        ]}],
        "checks": {
            "budget_compliance": {"Pip": 25},
        },
    },
    {
        "id": 6,
        "name": "Duplicate prevention — second add must be skipped",
        "owner_minutes": 60,
        "buffer": 5,
        "pets": [{"name": "Scout", "species": "dog", "tasks": [
            {"title": "Morning walk", "duration": 20, "priority": "high"},
        ]}],
        "checks": {
            "duplicate_skipped": {"pet": "Scout", "title": "Morning walk",
                                  "duration": 20, "priority": "high"},
        },
    },
    {
        "id": 7,
        "name": "Error handling — unknown pet name returns error",
        "owner_minutes": 60,
        "buffer": 5,
        "pets": [{"name": "Real", "species": "dog", "tasks": []}],
        "checks": {
            "error_on_unknown_pet": "Ghost",
        },
    },
    {
        "id": 8,
        "name": "Required flag passes through to task object",
        "owner_minutes": 60,
        "buffer": 5,
        "pets": [{"name": "Mochi", "species": "cat", "tasks": []}],
        "checks": {
            "required_flag": {"pet": "Mochi", "title": "Evening feeding",
                              "duration": 5, "priority": "high"},
        },
    },
]

# ── Result helpers ──────────────────────────────────────────────────────────

_PASS = "PASS"
_FAIL = "FAIL"


def _build_agent(scenario: dict) -> tuple[PawPalAgent, Owner]:
    owner = Owner(
        name="EvalOwner",
        available_minutes=scenario["owner_minutes"],
        buffer_minutes=scenario.get("buffer", 0),
    )
    for p in scenario["pets"]:
        pet = Pet(name=p["name"], species=p["species"])
        for t in p.get("tasks", []):
            pet.add_task(Task(
                title=t["title"],
                duration_minutes=t["duration"],
                priority=t["priority"],
            ))
        owner.pets.append(pet)
    return PawPalAgent(owner), owner


def _run_checks(scenario: dict) -> list[tuple[str, str, str]]:
    """Return list of (check_name, PASS/FAIL, detail)."""
    agent, owner = _build_agent(scenario)
    checks = scenario["checks"]
    results = []

    # -- Gap detection accuracy --
    if "gap_categories" in checks:
        for pet_name, expected_missing in checks["gap_categories"].items():
            result = agent._analyze_care_gaps(pet_name)
            actual = set(result.get("missing_categories", []))
            ok = actual == expected_missing
            detail = (
                f"expected {sorted(expected_missing) or '[]'}, "
                f"got {sorted(actual) or '[]'}"
            )
            results.append((f"gap_detection ({pet_name})", _PASS if ok else _FAIL, detail))

    # -- Budget compliance --
    if "budget_compliance" in checks:
        for pet_name, budget in checks["budget_compliance"].items():
            agent._add_recommended_task(pet_name, "Extra task A", 10, "medium")
            agent._add_recommended_task(pet_name, "Extra task B", 10, "low")
            sched = agent._generate_optimized_schedule(pet_name)
            used = sched.get("total_minutes_used", 9999)
            ok = used <= budget
            results.append((
                f"budget_compliance ({pet_name})",
                _PASS if ok else _FAIL,
                f"{used} min used, budget {budget} min",
            ))

    # -- Duplicate prevention --
    if "duplicate_skipped" in checks:
        c = checks["duplicate_skipped"]
        r = agent._add_recommended_task(c["pet"], c["title"], c["duration"], c["priority"])
        ok = r.get("status") == "skipped"
        results.append((
            "duplicate_prevention",
            _PASS if ok else _FAIL,
            f"status={r.get('status')}, reason={r.get('reason', '')}",
        ))

    # -- Error handling for unknown pet --
    if "error_on_unknown_pet" in checks:
        bad_name = checks["error_on_unknown_pet"]
        r1 = agent._analyze_care_gaps(bad_name)
        r2 = agent._add_recommended_task(bad_name, "Walk", 20, "medium")
        r3 = agent._generate_optimized_schedule(bad_name)
        ok = all("error" in r for r in (r1, r2, r3))
        results.append((
            "error_handling",
            _PASS if ok else _FAIL,
            "all three tools returned error dicts for unknown pet" if ok
            else "at least one tool did not return an error dict",
        ))

    # -- Required flag --
    if "required_flag" in checks:
        c = checks["required_flag"]
        agent._add_recommended_task(c["pet"], c["title"], c["duration"], c["priority"],
                                    required=True)
        pet = next(p for p in owner.pets if p.name == c["pet"])
        added = next((t for t in pet.tasks if t.title == c["title"]), None)
        ok = added is not None and added.required is True
        results.append((
            "required_flag",
            _PASS if ok else _FAIL,
            f"required={added.required if added else 'task not found'}",
        ))

    return results


# ── Report printing ─────────────────────────────────────────────────────────

def _print_report(all_results: list[tuple[int, str, list]]) -> None:
    col_w = 42
    print()
    print("=" * 70)
    print("  PawPal+ AI Agent — Evaluation Report")
    print("=" * 70)

    total_pass = total_fail = 0

    for scenario_id, scenario_name, checks in all_results:
        print(f"\nScenario {scenario_id}: {scenario_name}")
        for check_name, outcome, detail in checks:
            label = f"  {check_name}".ljust(col_w)
            marker = "✓" if outcome == _PASS else "✗"
            print(f"{label} {marker} {outcome}   {detail}")
            if outcome == _PASS:
                total_pass += 1
            else:
                total_fail += 1

    total = total_pass + total_fail
    pct = 100 * total_pass / total if total else 0

    print()
    print("-" * 70)
    print(f"  Result: {total_pass} / {total} checks passed  ({pct:.0f}%)")
    if total_fail == 0:
        print("  All checks passed.")
    else:
        print(f"  {total_fail} check(s) failed — see details above.")
    print("=" * 70)
    print()


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    all_results = []
    for scenario in SCENARIOS:
        checks = _run_checks(scenario)
        all_results.append((scenario["id"], scenario["name"], checks))
    _print_report(all_results)
