"""
PawPal+ AI Care Agent — agentic workflow using Claude tool use.

Workflow:
1. Reads the current owner/pet/task state via tool call
2. Identifies care gaps per pet (exercise, feeding, grooming, health, enrichment)
3. Adds missing tasks directly to the pet objects (mutates session state)
4. Generates an optimized schedule for each pet using the updated task list
5. Returns a structured result with the agent's analysis and final Plans

The key integration point: add_recommended_task and generate_optimized_schedule
both operate on the live Owner/Pet objects, so every AI action is immediately
reflected in the app's session state.
"""

import json
import os
import anthropic
from pawpal_system import Owner, Task, Scheduler

_CARE_CATEGORIES: dict[str, set[str]] = {
    "exercise":   {"walk", "run", "jog", "play", "fetch", "exercise", "stroll", "outdoor", "active"},
    "feeding":    {"feed", "food", "meal", "treat", "water", "drink", "eat"},
    "grooming":   {"groom", "brush", "bath", "wash", "nail", "clean", "comb", "trim"},
    "health":     {"medicine", "med", "pill", "dose", "vet", "checkup", "health", "vaccine", "inspect"},
    "enrichment": {"train", "training", "cuddle", "snuggle", "toy", "game", "puzzle", "socializ", "bond"},
}

_TOOLS = [
    {
        "name": "get_pets_and_tasks",
        "description": (
            "Get the current state of all pets and their pending task lists. "
            "Call this first before analyzing any pet."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "analyze_care_gaps",
        "description": (
            "Analyze a specific pet's pending tasks and identify which care categories "
            "(exercise, feeding, grooming, health, enrichment) are missing. "
            "Call this for each pet before adding tasks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_name": {"type": "string", "description": "Name of the pet to analyze"},
            },
            "required": ["pet_name"],
        },
    },
    {
        "name": "add_recommended_task",
        "description": (
            "Add a task to fill an identified care gap. This directly modifies the pet's "
            "live task list — the task will appear in the schedule. Only add tasks for "
            "categories confirmed as missing by analyze_care_gaps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_name": {"type": "string"},
                "title": {
                    "type": "string",
                    "description": "Specific, descriptive task name (e.g. 'Evening walk', 'Morning feeding')",
                },
                "duration_minutes": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 60,
                    "description": "Realistic duration: feeding 5–10 min, grooming 10–15 min, exercise 15–30 min",
                },
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "required": {
                    "type": "boolean",
                    "description": "True only for essential daily tasks like feeding",
                },
            },
            "required": ["pet_name", "title", "duration_minutes", "priority"],
        },
    },
    {
        "name": "generate_optimized_schedule",
        "description": (
            "Generate an optimized daily schedule for a pet using its current task list, "
            "including any tasks you just added. Call this for each pet after all tasks "
            "have been added."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_name": {"type": "string"},
            },
            "required": ["pet_name"],
        },
    },
]

_SYSTEM_PROMPT = """\
You are PawPal+'s AI Care Agent. Your job is to ensure every pet has a complete, \
well-rounded daily care schedule by finding gaps and filling them intelligently.

Follow this exact workflow:
1. Call get_pets_and_tasks once to see the full current state.
2. Call analyze_care_gaps for each pet to identify missing care categories.
3. Call add_recommended_task for each missing category — one task per gap, \
   tailored to the pet's species. Never add duplicates.
4. Call generate_optimized_schedule for each pet after all tasks have been added.
5. Write a concise, specific summary covering: which gaps you found per pet, \
   which tasks you added and why, and a brief note on each pet's final schedule \
   (minutes used, tasks scheduled, anything notable).

Critical rules:
- Only add tasks for categories genuinely missing from the current task list.
- Mark feeding tasks as required=true; all others false unless clearly essential.
- Keep task titles specific and natural (e.g. "Morning walk" not "Exercise").
- Act immediately — do not ask for confirmation before adding tasks.\
"""


class PawPalAgent:
    """Runs the agentic care-gap-filling and scheduling workflow."""

    def __init__(self, owner: Owner):
        self.owner = owner
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.added_tasks: list[dict] = []
        self.generated_plans: dict = {}  # pet_name → Plan

    # ------------------------------------------------------------------
    # Tool implementations — operate on live Owner/Pet objects
    # ------------------------------------------------------------------

    def _get_pets_and_tasks(self) -> dict:
        return {
            pet.name: {
                "species": pet.species,
                "pending_tasks": [
                    {
                        "title": t.title,
                        "duration_minutes": t.duration_minutes,
                        "priority": t.priority,
                        "required": t.required,
                    }
                    for t in pet.tasks
                    if t.status == "pending"
                ],
            }
            for pet in self.owner.pets
        }

    def _analyze_care_gaps(self, pet_name: str) -> dict:
        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            return {"error": f"Pet '{pet_name}' not found"}

        pending = [t for t in pet.tasks if t.status == "pending"]
        covered: set[str] = set()
        for task in pending:
            lower = task.title.lower()
            for category, keywords in _CARE_CATEGORIES.items():
                if any(kw in lower for kw in keywords):
                    covered.add(category)

        missing = sorted(set(_CARE_CATEGORIES.keys()) - covered)
        return {
            "pet": pet_name,
            "species": pet.species,
            "covered_categories": sorted(covered),
            "missing_categories": missing,
            "available_minutes": self.owner.available_minutes,
        }

    def _add_recommended_task(
        self,
        pet_name: str,
        title: str,
        duration_minutes: int,
        priority: str,
        required: bool = False,
    ) -> dict:
        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            return {"error": f"Pet '{pet_name}' not found"}

        lower_title = title.strip().lower()
        if any(t.title.lower() == lower_title and t.status == "pending" for t in pet.tasks):
            return {"status": "skipped", "reason": f"'{title}' is already pending for {pet_name}"}

        task = Task(
            title=title.strip(),
            duration_minutes=int(duration_minutes),
            priority=priority,
            required=required,
        )
        pet.add_task(task)
        self.added_tasks.append({
            "pet": pet_name,
            "title": title.strip(),
            "duration_minutes": int(duration_minutes),
            "priority": priority,
            "required": required,
        })
        return {"status": "added", "pet": pet_name, "task": title, "duration_minutes": duration_minutes}

    def _generate_optimized_schedule(self, pet_name: str) -> dict:
        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            return {"error": f"Pet '{pet_name}' not found"}

        plan = Scheduler(owner=self.owner, pet=pet).generate_plan()
        self.generated_plans[pet_name] = plan

        return {
            "pet": pet_name,
            "tasks_scheduled": len(plan.selected_tasks),
            "total_minutes_used": plan.total_minutes_used,
            "schedule": [
                {"task": t.title, "start_min": s, "end_min": e, "priority": t.priority}
                for t, s, e in plan.get_time_slots()
            ],
        }

    def _dispatch(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "get_pets_and_tasks":
            result = self._get_pets_and_tasks()
        elif tool_name == "analyze_care_gaps":
            result = self._analyze_care_gaps(tool_input["pet_name"])
        elif tool_name == "add_recommended_task":
            result = self._add_recommended_task(
                pet_name=tool_input["pet_name"],
                title=tool_input["title"],
                duration_minutes=tool_input["duration_minutes"],
                priority=tool_input["priority"],
                required=tool_input.get("required", False),
            )
        elif tool_name == "generate_optimized_schedule":
            result = self._generate_optimized_schedule(tool_input["pet_name"])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        return json.dumps(result)

    # ------------------------------------------------------------------
    # Agentic loop
    # ------------------------------------------------------------------

    def run(self) -> dict:
        """
        Run the agentic loop until Claude signals end_turn.
        Returns a dict with keys: summary, added_tasks, plans.
        """
        pet_names = [p.name for p in self.owner.pets]
        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyze the care schedule for {self.owner.name}'s pet(s): "
                    f"{', '.join(pet_names)}. "
                    f"Available time today: {self.owner.available_minutes} min "
                    f"(buffer between tasks: {self.owner.buffer_minutes} min). "
                    "Fill any care gaps and generate optimized schedules."
                ),
            }
        ]

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                tools=_TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                summary = next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    "",
                )
                return {
                    "summary": summary,
                    "added_tasks": self.added_tasks,
                    "plans": self.generated_plans,
                }

            if response.stop_reason == "tool_use":
                tool_results = [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": self._dispatch(block.name, block.input),
                    }
                    for block in response.content
                    if block.type == "tool_use"
                ]
                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop — return whatever we have
                break

        return {"summary": "", "added_tasks": self.added_tasks, "plans": self.generated_plans}
