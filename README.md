# PawPal+ 🐾 — AI-Enhanced Pet Care Scheduling

## Original Project & Summary

**Original Project:** PawPal+ is a Streamlit-based pet care scheduling application that helps pet owners organize daily tasks for multiple pets within a constrained time budget. It uses a 0/1 knapsack optimization algorithm to select the highest-value combination of tasks (feeding, walking, grooming, etc.) that fits the available time while guaranteeing that required tasks are always included. The original system supports multiple pets with species filtering, priority-based task ranking, buffer time between tasks, and automatic conflict detection across multi-pet schedules.

## What This Project Does & Why It Matters

**PawPal+ with AI Care Agent** extends the original scheduling system with intelligent, Claude-powered gap analysis. While the original app required users to manually enter all tasks, the new **AI Care Agent** automatically analyzes a pet's current task list, identifies missing care categories (exercise, feeding, grooming, health, enrichment), and recommends specific tasks to fill those gaps. This transforms pet care planning from a manual checklist into an intelligent advisory system—ensuring no pet's critical care needs are overlooked, while still respecting time constraints and user priorities.

**Why it matters:** Pet owners often forget routine care tasks or don't think holistically about all their pet's needs. The AI agent acts as a caring assistant that reviews the plan comprehensively and suggests what's missing, making daily pet care safer, more complete, and less stress for the owner.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      Streamlit UI (app.py)                        │
│                                                                   │
│  Step 1: Owner setup  →  Step 2: Add pets  →  Step 3: Add tasks │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Step 4: AI Care Agent (NEW)                             │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ PawPalAgent + Claude Tool Use (ai_advisor.py)       │ │  │
│  │  │                                                      │ │  │
│  │  │ 1. get_pets_and_tasks() → reads current state      │ │  │
│  │  │ 2. analyze_care_gaps() → per-pet missing categories │ │  │
│  │  │ 3. add_recommended_task() → mutates pet.tasks      │ │  │
│  │  │ 4. generate_optimized_schedule() → Scheduler.Plan  │ │  │
│  │  │                                                      │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  All AI actions mutate session state → Schedule rendered  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Step 5: Generate schedule  →  Step 6: Mark tasks complete      │
└──────────────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
    ┌─────────────────┐           ┌──────────────┐
    │  pawpal_system  │           │ PawPalAgent  │
    │                 │           │              │
    │ Owner           │           │ Tool Use:    │
    │ Pet             │◄──────────│ Dispatch     │
    │ Task            │           │ Calls        │
    │ Scheduler       │           │              │
    │ Plan            │           │ Claude SDK   │
    └─────────────────┘           └──────────────┘
         │
         ▼ (0/1 Knapsack DP)
      Plan (optimized schedule)
         │
         ▼ (Rendered as)
    Colored HTML table with task emojis,
    priority badges, required indicators,
    time slots, and AI-added badges (🤖)
```

**Key components:**

- **pawpal_system.py** — Core scheduling classes: Owner, Pet, Task, Scheduler, Plan. Implements 0/1 knapsack optimization and conflict detection.
- **ai_advisor.py (NEW)** — PawPalAgent class that orchestrates an agentic loop with Claude, using tool use to read pet state, analyze care gaps, add recommended tasks, and generate schedules.
- **app.py** — Streamlit UI with six integrated steps. Step 4 (new) invokes the AI agent; the resulting tasks are merged into the app state and marked with a 🤖 badge.

---

## Setup Instructions

### 1. Clone and install dependencies

```bash
git clone <repository>
cd applied-ai-system-final

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Set up Claude API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # Get yours from https://console.anthropic.com
```

On Windows (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### 4. (Optional) Run tests

```bash
python -m pytest tests/test_pawpal.py -v
```

---

## Sample Interactions

### Example 1: AI Agent Fills Exercise & Enrichment Gaps

**User Setup:**

- Owner: "Jordan" with 120 minutes available
- Pet: "Mochi" (dog)
- User-added tasks:
  - Morning feeding (5 min, high priority, required)
  - Evening feeding (5 min, high priority, required)
  - Brushing (10 min, medium priority)

**User clicks "Run AI Care Agent"**

**AI Agent Workflow:**

```
Claude: "I'll analyze Mochi's care schedule..."

Tool Call 1: get_pets_and_tasks()
→ Returns: Mochi (dog) has 3 pending tasks in feeding and grooming

Tool Call 2: analyze_care_gaps(pet_name="Mochi")
→ Returns:
  covered_categories: ["feeding", "grooming"]
  missing_categories: ["enrichment", "exercise", "health"]

Tool Call 3: add_recommended_task(
  pet_name="Mochi",
  title="Morning walk",
  duration_minutes=25,
  priority="high",
  required=False
)
→ Status: added

Tool Call 4: add_recommended_task(
  pet_name="Mochi",
  title="Evening walk",
  duration_minutes=25,
  priority="high",
  required=False
)
→ Status: added

Tool Call 5: add_recommended_task(
  pet_name="Mochi",
  title="Play fetch",
  duration_minutes=15,
  priority="medium",
  required=False
)
→ Status: added

Tool Call 6: generate_optimized_schedule(pet_name="Mochi")
→ Returns optimized plan with all tasks scheduled

Claude Summary:
"✨ Mochi was missing exercise, enrichment, and health checks. I added:
- **Morning walk** (25 min) to ensure daily exercise
- **Evening walk** (25 min) for evening activity
- **Play fetch** (15 min) for enrichment and bonding

Your schedule now covers all five care categories. Total time used: 95 min out of 120 available."
```

**Result in UI:**

- ✨ Agent added **3 task(s)** to fill care gaps
- Task list now shows 🤖 badges next to: "Morning walk", "Evening walk", "Play fetch"
- Generated schedule shows all 6 tasks fitting within 120 minutes
- Summary expands to show Claude's analysis

---

### Example 2: Multiple Pets with Partial Gaps

**User Setup:**

- Owner: "Alex" with 180 minutes available
- Pet 1: "Rex" (dog) with existing tasks: Walk (20 min), Feed (5 min)
- Pet 2: "Whiskers" (cat) with existing tasks: Feed (5 min), Litter box maintenance (3 min)

**User clicks "Run AI Care Agent"**

**AI Agent Results:**

For **Rex (dog):**

- Covered: Exercise (walk), Feeding
- Missing: Grooming, Health, Enrichment
- Agent adds: "Brushing" (10 min), "Play tug-of-war" (15 min)

For **Whiskers (cat):**

- Covered: Feeding, Litter maintenance
- Missing: Exercise, Grooming, Enrichment, Health
- Agent adds: "Indoor play session" (10 min), "Brush Whiskers" (5 min), "Check paws & ears" (5 min)

**Schedule Output:**

```
Rex (dog) — 50 min used, 5 tasks scheduled
  Morning walk (20 min)
  Brushing (10 min)
  Play tug-of-war (15 min)
  Feed Rex (5 min)

Whiskers (cat) — 28 min used, 6 tasks scheduled
  Feed Whiskers (5 min)
  Litter box maintenance (3 min)
  Indoor play session (10 min)
  Brush Whiskers (5 min)
  Check paws & ears (5 min)

✅ No scheduling conflicts across pets.
Total time used: 78 min out of 180 available.
```

---

### Example 3: AI Avoids Duplicates & Respects User Choices

**User Setup:**

- Owner has 60 minutes available
- Pet: "Buddy" with tasks: "Walk" (20 min), "Feed" (5 min), "Walk" (duplicate, pending)

**User clicks "Run AI Care Agent"**

**AI Agent Behavior:**

- Tool `analyze_care_gaps` finds: covered=[Exercise (walk), Feeding], missing=[Grooming, Health, Enrichment]
- Tool `add_recommended_task` tries to add "Brushing" → Status: added
- Tool `add_recommended_task` tries to add "Play time" → Status: added
- Tool `generate_optimized_schedule` builds a plan that includes:
  - Required: Feed (5 min)
  - Selected via knapsack: Walk (20 min), Brushing (10 min), Play time (15 min)
  - Skipped: one duplicate "Walk" (already a pending task, filtered by UI duplicate check)

**Output:**

```
✨ Agent added **2 task(s)** to fill care gaps:
- **Buddy**: Brushing (medium priority, 10 min)
- **Buddy**: Play time (low priority, 15 min)

Schedule: 50 min used (walk + feed + brushing + play time)
Explanation: Required task "Feed" always included. Brushing covers missing grooming gap.
Play time fills enrichment. One duplicate walk was skipped.
```

---

## Design Decisions

### Original System (PawPal+)

1. **0/1 Knapsack over Greedy**
   - _Why:_ A greedy "pick by priority until time runs out" approach fails when a single high-priority task blocks multiple shorter tasks with higher combined value.
   - _Trade-off:_ Knapsack DP is more complex (O(n\*budget)) but finds optimal solutions; greedy is simpler but suboptimal. We chose correctness because poor scheduling directly affects pet care quality.

2. **Species Filtering as Hard Pre-Filter**
   - _Why:_ A task marked "dog-only" should never appear for cats, period. This is not a weighted preference; it's a safety guarantee.
   - _Trade-off:_ Filters tasks before knapsack rather than penalizing ineligible tasks in the DP. Simpler and more explicit.

3. **Staggered Multi-Pet Schedules**
   - _Why:_ Each pet's plan is optimized independently, then sequenced one after another (Pet 1: 0–50 min, Pet 2: 55–100 min, with buffer). Avoids false conflicts and keeps each pet's schedule locally optimal.
   - _Trade-off:_ Reactive conflict detection rather than joint optimization. Could allow interleaving (feed cat while dog rests), but that complexity isn't worth it for typical households. Users are warned of any genuine overlaps.

### New: AI Care Agent (ai_advisor.py)

1. **Tool Use Instead of Direct API Calls**
   - _Why:_ Claude's tool use interface lets the agent autonomously decide which actions to take (get state, analyze gaps, add tasks, schedule). This creates a clean feedback loop where Claude processes its own results.
   - _Trade-off:_ More code than simple text generation, but gives Claude agency and ensures actions are traced.

2. **Agentic Loop with `while True` + Stop Reason**
   - _Why:_ The agent runs until Claude signals `end_turn`. If it calls a tool, we dispatch it and loop. This lets Claude call multiple tools in sequence (e.g. analyze gaps for Pet A, add tasks, analyze gaps for Pet B, add tasks, schedule both).
   - _Trade-off:_ More complex than a single API call, but necessary for multi-step workflows. We could add a max-iteration guard for safety.

3. **Mutation of Session State**
   - _Why:_ When the agent calls `add_recommended_task`, it directly modifies the live `owner.pets[pet].tasks` list. This means every AI action is instantly reflected in the app's session state without a separate merge step.
   - _Trade-off:_ Tightly couples the AI agent to Streamlit's session state. Alternative: agent returns a list of new tasks and the app merges them. We chose direct mutation for simplicity and immediacy (user sees tasks added in real-time).

4. **Care Categories as Regex-Based Keywords**
   - _Why:_ No need for a separate ML classifier. The agent analyzes task titles against hard-coded keyword sets (e.g. "walk", "run", "fetch" → exercise). Fast, deterministic, and easy to debug.
   - _Trade-off:_ Brittle if titles don't match keywords. Could use NLP or an LLM call to classify, but that adds latency and cost. Current approach works for natural language task names.

5. **System Prompt Guides Claude's Workflow**
   - _Why:_ The prompt explicitly tells Claude to follow 4 steps: (1) get state, (2) analyze gaps, (3) add tasks, (4) schedule. This reduces hallucination and keeps Claude on track.
   - _Trade-off:_ Rigid workflow; Claude can't deviate. But for a pet care planner, predictability is more valuable than flexibility.

---

## Testing Summary

### Original System Tests (21 tests in `tests/test_pawpal.py`)

**What Worked:**

- ✅ Task sorting maintained correctly after every `add_task` call
- ✅ Required tasks always included even when they exceed budget
- ✅ 0/1 knapsack correctly selects optimal task combinations (verified against greedy failures)
- ✅ Species filtering excludes ineligible tasks before scheduling
- ✅ Conflict detection identifies overlapping time slots accurately
- ✅ Buffer time correctly added between tasks
- ✅ Recurring tasks spawn next occurrence with correct due_date

**What Didn't Work (Initially):**

- ❌ Multi-pet schedules showed false conflicts because every pet started at minute 0
  - _Fix:_ Added `start_offset` to Plan class to stagger schedules
- ❌ Greedy scheduler sometimes selected one long task, blocking multiple shorter ones
  - _Fix:_ Switched to 0/1 knapsack DP
- ❌ No validation on input (invalid priority, negative duration)
  - _Fix:_ Added `__post_init__` validation in Owner, Pet, Task

**Test Coverage Confidence: 5/5 stars**

- High confidence in common cases (single pet, multiple pets, required tasks, species filtering)
- Lower confidence in edge cases: Owner with 1 minute available and a 5-minute required task (plan should include it anyway)

### AI Agent Testing (Manual)

**What Worked:**

- ✅ Agent successfully calls `get_pets_and_tasks()` and reads live state
- ✅ `analyze_care_gaps()` correctly identifies covered and missing categories
- ✅ `add_recommended_task()` mutates the session state; tasks appear immediately in the schedule
- ✅ `generate_optimized_schedule()` produces plans that fit the budget
- ✅ Agent stops after one iteration when analysis is complete
- ✅ 🤖 badges correctly label AI-added tasks in the UI

**What Could Be Improved:**

- ⚠️ No retry logic if Claude's tool calls fail (e.g. invalid pet_name)
  - Current: Agent returns error in tool result; Claude should recognize and retry, but we haven't tested this thoroughly
- ⚠️ No max-iteration guard; agent could loop indefinitely if Claude keeps calling tools
  - Current: Relies on Claude's `end_turn` signal; works in practice but not hardened
- ⚠️ Care gap analysis is keyword-based; could miss tasks with non-standard titles
  - Example: A task titled "Fido's spa day" might not match grooming keywords; agent wouldn't recognize it as grooming

**What I Learned:**

1. Claude's tool use is surprisingly reliable; the agent rarely hallucinates or calls the wrong tool
2. The system prompt's explicit workflow (4 steps) is crucial; without it, Claude sometimes skips steps
3. Agentic workflows are easier to debug when each tool prints its result to the UI (transparency builds trust)

---

## Reflection: What This Project Taught Me

### About AI & Agentic Systems

**1. Tool Use Enables Autonomy**

- Generating text with "the tasks the agent recommends are X, Y, Z" is passive. Giving Claude tools to actually _do_ things (call functions, mutate state, trigger schedules) transforms it into an active agent. The difference is profound: the agent becomes responsible for its decisions, not just suggesting them.

**2. Structured Prompts + Tool Schema = Guardrails**

- Without explicit system prompts, Claude sometimes skips steps or calls tools in the wrong order. With a clear workflow and well-defined tool schemas (required fields, enums for priority), the agent stays on track. The 4-step prompt (get state → analyze → add → schedule) cut debugging time significantly.

**3. State Mutations Must Be Traceable**

- Directly mutating `owner.pets[0].tasks` inside the agent is convenient but risky. If the agent crashes mid-mutation, the app is left in an inconsistent state. A safer pattern: agent returns a list of new tasks, the app decides whether to merge them. For a prototype, direct mutation is fine; for production, build an audit trail.

### About Problem-Solving & Design

**4. User Empathy Shapes the Architecture**

- The original PawPal+ forces users to think about all their pet's care needs upfront. The AI agent removes that burden by offering suggestions. This is not just a UX improvement; it's a design philosophy: _detect what the user forgot, then offer to fix it_. This philosophy should inform every feature.

**5. Simplicity > Generality**

- I initially considered building a complex classifier to recognize care categories from task titles (ML model, LLM-based classification). Instead, regex keyword matching is fast, deterministic, and works. The lesson: start simple, add complexity only when simple breaks. This project didn't need NLP; keywords were enough.

**6. Agentic Workflows Require Different Debugging**

- Debugging `generate_plan()` is straightforward: print the inputs, trace the DP, check the output. Debugging the agentic loop is different. You need to see what Claude is thinking (its response), what tools it called, and what each tool returned. Transparent logging of the entire loop is essential.

### About Working with Claude

**7. Specific Questions Yield Better Answers**

- "How do I implement 0/1 knapsack?" → clear, focused answer with pseudocode.
- "Make the scheduler better" → vague suggestions that don't fit the project.
- The difference: a specific question gives Claude a frame of reference; an open-ended one leaves Claude guessing at your intent.

**8. Treat Claude as a Collaborator, Not an Oracle**

- Claude suggested raising an exception if a plan is None (early project). I rejected it because Streamlit errors wipe the user's session. Instead, I kept error paths as warning strings. This taught me: _Claude's suggestions are starting points, not final decisions. My judgment about trade-offs (crash vs. warning) is the real value-add._

**9. Fresh Context per Phase Helps**

- I kept separate chat sessions for design, algorithm, debugging, and integration. Each phase got its own session to avoid stale context. Switching from "how should I structure classes?" to "why is the knapsack failing?" on a fresh session forced me to rearticulate the problem, which often clarified my thinking before Claude even responded.

### Key Takeaway

**The best AI-assisted projects are led by humans with clear vision, not driven by AI's suggestions.** Claude and tool use are powerful accelerators: they help you implement faster, debug more systematically, and explore alternatives without running out of ideas. But the person at the keyboard has to stay in control of the design. Use AI to answer specific questions, not to decide what the project should be.

---

## File Structure

```
applied-ai-system-final/
├── README.md                  # This file
├── reflection.md              # Detailed design & learning reflection
├── requirements.txt           # Python dependencies
├── pawpal_system.py          # Core scheduling system (Owner, Pet, Task, Scheduler, Plan)
├── ai_advisor.py             # AI Care Agent with Claude tool use
├── app.py                    # Streamlit UI with 6 integrated steps
├── main.py                   # Legacy entry point (for non-Streamlit use)
├── tests/
│   ├── __init__.py
│   └── test_pawpal.py        # 21 unit tests
├── screenshots/              # Demo images
├── assets/                   # App-related assets (new)
└── uml_final.png            # System architecture diagram
```

---

## Troubleshooting

**"AI Care Agent is grayed out / says 'Set ANTHROPIC_API_KEY'"**

- Ensure `ANTHROPIC_API_KEY` is exported before running `streamlit run app.py`
- Verify key is valid at https://console.anthropic.com
- Restart the Streamlit app after setting the key

**"AI agent added tasks I don't want"**

- Tasks can be removed manually in Step 3 (task removal dropdown)
- AI recommendations are suggestions, not commands; you have full control

**"Schedule shows conflicts even after AI agent ran"**

- Multi-pet conflicts are detected reactively. If the warning persists, try:
  - Increasing `available_minutes` for the owner
  - Removing lower-priority tasks manually
  - Reducing task durations

**Tests fail with "ModuleNotFoundError: anthropic"**

- Run `pip install -r requirements.txt` in the active venv

---

## Future Enhancements

1. **Joint Multi-Pet Scheduling** — Currently pets are scheduled sequentially. A true joint optimizer could interleave tasks.
2. **Real Clock Times** — Display time slots as "8:00 AM – 8:20 AM" instead of "0–20 min offset".
3. **Persistent Storage** — Save schedules and recurring tasks across sessions.
4. **AI Personalization** — Let Claude learn the user's pet care style over time (e.g. "you prefer longer walks, fewer play sessions").
5. **Mobile App** — Streamlit on mobile is limited; a native React/Flutter app would improve on-the-go task tracking.

---

## Contributing

Pull requests welcome! Please include tests for any new features and update this README if you change the architecture.

## License

MIT

---

**Questions?** See `reflection.md` for deeper dives into design decisions, testing strategy, and AI integration learnings.
