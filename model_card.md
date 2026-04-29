# PawPal+ Model Card

## System Overview

**System name:** PawPal+ AI Care Agent
**Model used:** Claude claude-sonnet-4-6 (Anthropic)
**Task:** Agentic pet care schedule analysis — identifies missing care categories, adds recommended tasks, and generates optimized daily plans using Claude tool use.

---

## AI Collaboration

**How I used AI during development**

I used AI at every stage of the project. During design, I described the problem and asked what class structure would make sense, which helped me settle on the Owner → Pet → Task hierarchy quickly. During algorithm selection, I asked why a greedy scheduler would fail for this problem and what alternatives existed — the explanation of 0/1 knapsack DP was clear and directly usable. During debugging, I described symptoms (multi-pet schedules always showing conflicts, every pet starting at minute 0) and used the AI to identify root causes. During code review, I pasted individual methods and asked whether edge cases were handled correctly.

The most useful prompts were specific and included the actual code or error message. Vague prompts like "make it better" produced suggestions that did not fit the project's constraints. Questions like "what happens if required tasks alone exceed available_minutes?" produced concrete, usable answers.

**One helpful AI suggestion**

When designing the agentic workflow, I asked whether schedule generation should happen inside the agent loop or after it finishes. The suggestion was to make `generate_optimized_schedule` a tool the agent calls itself rather than running the scheduler automatically once the loop ended. That turned out to be the right call — it means the agent receives the actual schedule as a tool result and can reference specific tasks and times in its final summary, which made the explanations much more grounded and specific than they would have been otherwise.

**One flawed AI suggestion**

Early on, the AI suggested building a vector database (FAISS or ChromaDB) to store a pet care knowledge base for RAG-style retrieval. The idea was that the agent would search this knowledge base before recommending tasks. For the actual problem — identifying five fixed care categories from a short task title list — that was a large infrastructure investment for no real benefit. A keyword lookup over a small dictionary solved the same problem in ten lines and was far easier to test and reason about. I rejected the suggestion and kept the simpler approach. It was a good reminder that the AI tends to reach for powerful tools even when a simpler one fits better, and that matching the tool to the actual complexity of the problem is a judgment call the developer has to make.

---

## Limitations and Biases

**Keyword matching is brittle.** The agent identifies missing care categories by scanning task titles for known words (e.g. "walk" → exercise, "feed" → feeding). A task titled "agility course" would not register as exercise, so the agent might incorrectly flag that category as missing and add a redundant task. It works well for plain, common task names but breaks with creative or unusual wording.

**The five care categories are fixed.** Exercise, feeding, grooming, health, and enrichment are hardcoded. They do not account for species-specific needs beyond the three supported types, or for pets with medical conditions or age-related routines that fall outside those buckets.

**Claude's suggestions reflect its training data.** The LLM recommends tasks based on patterns in its training data, which skews toward common domestic pet norms. A 30-minute walk might be appropriate for a young Labrador but wrong for a senior small-breed dog. The agent has no way to distinguish them because it only sees a name and species.

**Misuse and guardrails.** The most realistic risk is the agent adding tasks that are unnecessary or subtly wrong. Three design decisions reduce this risk: the agent can only add tasks to fill identified gaps and cannot modify or delete anything the owner entered; every AI-added task is marked with a 🤖 badge so the owner can remove any before running the final schedule; and the Scheduler enforces the time budget regardless of how many tasks the agent adds, so over-recommendations are automatically trimmed by the knapsack.

---

## Testing Results

**Automated test suite — 39 tests, 39 passed**

- `tests/test_pawpal.py` (21 tests) — core scheduling system: task sorting, required task inclusion, knapsack optimality, species filtering, conflict detection, buffer accounting, and recurring task logic.
- `tests/test_ai_advisor.py` (18 tests) — AI agent tool layer: gap detection accuracy, task mutation, duplicate prevention (including case-insensitive matching), budget compliance, error handling for unknown pets, and required flag propagation.

**Evaluation harness — 8 / 8 scenarios passed**

`eval_harness.py` runs the agent's tool layer against eight predefined scenarios without making any API calls:

| Scenario | Check | Result |
|---|---|---|
| Dog with no tasks | All 5 gaps detected | PASS |
| Cat with feeding only | 4 gaps detected | PASS |
| Dog with exercise + feeding | 3 gaps detected | PASS |
| Fully covered pet | 0 gaps detected | PASS |
| Tight budget (25 min) | Schedule stays within budget | PASS |
| Duplicate task | Second add correctly skipped | PASS |
| Unknown pet name | All tools return error dict | PASS |
| Required flag | Passes through to Task object | PASS |

**What surprised me while testing**

The duplicate check needed to be case-insensitive. A test using "Morning Walk" and "morning walk" as separate entries revealed that a simple string comparison would have added both — a subtle bug the user would not notice until the schedule showed the same task twice. Catching it through a test before it reached the UI was exactly the kind of thing testing is for.

It was also not obvious how important it was to filter out completed tasks before checking care gaps. An early version counted completed tasks as covering their category, meaning an owner who had already completed the morning walk would not get an exercise gap flagged for the rest of the day. Filtering to pending tasks only fixed it, but the issue only surfaced through a test written specifically for that state.

---

## Future Improvements

- Replace keyword matching with an LLM-based classifier so gap detection works with any task wording.
- Build a joint multi-pet scheduler that interleaves tasks across pets rather than sequencing them one after another.
- Display schedule times as real clock times (e.g. "8:00 AM") rather than abstract minute offsets.
- Add a max-iteration guard to the agentic loop so it cannot run indefinitely if Claude keeps calling tools.
- Persist schedules and recurring tasks across sessions so the app retains state between visits.
