# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.  
  In my initial UML design, I structured the app around the main components needed to generate a pet care plan. I used the classes Owner, Pet, Task, Scheduler, Plan, and StreamlitUI.

- What classes did you include, and what responsibilities did you assign to each?

## a. Initial design

The Owner class represents the user of the app and stores information such as the owner’s name and available time. The available time is an important constraint because it determines how many tasks can be included in the daily plan.

The Pet class stores basic information about the pet, such as its name and type. This helps provide context for the tasks being planned.

The Task class represents individual pet care activities such as feeding, walking, grooming, or giving medicine. Each task includes a name, duration, and priority. These attributes allow the system to compare tasks and decide which ones are most important.

The Scheduler class is the core of the system. Its role is to take the list of tasks and the owner’s available time, then generate a daily plan by selecting the tasks that best fit within the time constraint. It also provides an explanation of why certain tasks were selected or skipped.

The Plan class represents the final output of the app. It stores the selected tasks, total time used, and the explanation of the scheduling decisions.

Finally, the StreamlitUI component represents the user interface. It is responsible for collecting input from the user and displaying the generated plan.

I designed the system this way so that each component has a clear responsibility, making the system easier to understand, organize, and extend.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.  
  Yes, my design changed in several meaningful ways during implementation.

1. The Scheduler's algorithm changed from greedy to 0/1 knapsack.  
   In the original skeleton, the scheduler sorted tasks by priority and duration, then greedily added tasks one by one until time ran out. This was simple but produced suboptimal plans. A single long high-priority task could block several shorter tasks that together would be more valuable. I replaced it with a dynamic programming knapsack algorithm that considers all combinations and selects the set of tasks with the highest total priority value that still fits within the available time. This was a more complex implementation but produces genuinely better schedules.

2. The Task class gained a species field.  
   The original Task had no awareness of which pet it applied to. I added an optional species field so that tasks like "walk the dog" could be marked as dog-only and automatically excluded when the pet is a cat. The Scheduler now filters tasks by species eligibility before scheduling, and the explanation separately reports tasks excluded for species mismatch versus tasks skipped due to time.

3. The Plan class gained owner and pet fields.  
   In the skeleton, Plan only stored selected_tasks, total_minutes_used, and explanation. The final implementation added owner and pet so that the plan is self-contained. It carries all the context needed to display or summarize the result without passing the owner and pet separately to the UI.

4. Input validation was added to Owner, Pet, and Task.
   The initial skeletons were plain dataclasses with no validation. I added **post_init** methods to enforce that available_minutes and duration_minutes are positive, that priority is one of {"high", "medium", "low"}, and that species is one of {"dog", "cat", "other"}. This prevents silent bugs caused by bad input reaching the scheduler.

5. A `start_offset` field was added to Plan to fix multi-pet scheduling conflicts.
   Every pet's plan originally started its time slots at minute 0, which caused every multi-pet schedule to report false conflicts. Adding `start_offset` to `Plan` and advancing it after each pet's last task means each pet's schedule picks up where the previous one left off, so the conflict detector only fires on genuine overlaps.

6. The UI grew significantly beyond the initial skeleton.
   The original design had a minimal Streamlit interface. During implementation it expanded to include: duplicate task prevention (warns and blocks re-adding a pending task with the same name), remove pet and remove task controls, a dedicated "Mark tasks complete" section that resets on every new schedule generation, persistent schedule display stored in `st.session_state` so the schedule survives page interactions, and color-coded task tables using `tabulate` to generate priority-highlighted HTML rows.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three main constraints:

1. **Time** — the owner's `available_minutes` is the hard outer limit. No plan can exceed it. When multiple pets exist, the budget is divided proportionally based on how many tasks each pet has pending.
2. **Priority** — tasks are labeled high, medium, or low. The knapsack algorithm maximizes total priority value (high=3, medium=2, low=1), so a set of two medium-priority tasks can outweigh a single high-priority task if they fit better in the remaining time.
3. **Required flag** — tasks marked `required=True` are always included, regardless of time pressure. Their cost is deducted from the budget first, and the remaining time is handed to the knapsack for optional tasks.
4. **Species eligibility** — a task with a `species` field set is excluded for pets of a different species before scheduling begins. This is a hard filter, not a weighted preference.

Time came first in priority because it is the only truly hard constraint. The owner cannot create more hours in a day. Required tasks came second because they represent non-negotiable care (e.g. feeding, medication). Priority value came third and is used to rank optional tasks when time is tight. Species eligibility is a pre-filter and does not interact with the knapsack at all.

**b. Tradeoffs**.

**Tradeoff: Conflict detection is reactive, not preventive.**

The scheduler creates each pet's plan separately, giving each pet its fair share of the owner's available time. After that, it checks the schedules for any overlapping tasks. If it finds overlaps, it just reports a warning. It doesn't try to fix the problem by rescheduling anything.

This approach makes sense for a daily pet care planner because most people have just one pet, and in that case, there can't be any conflicts within a single pet's schedule by design. For households with multiple pets, the way time is divided proportionally already helps avoid overlaps without needing a complicated joint scheduling system. Using reactive detection keeps each pet's plan straightforward and optimized individually, while still letting the user know about any issues. Trying to prevent conflicts upfront by finding a perfect schedule for all pets at once would be way too complex and unnecessary for a typical home with a couple of pets whose care doesn't need to be coordinated down to the minute.  

---

## 3. AI Collaboration

**a. How you used AI**

I used AI tools at several stages of the project:

- **Design brainstorming** — early on I described the problem (pet care planning with time and priority constraints) and asked what data structures and class responsibilities would make sense. This helped me settle on the Owner → Pet → Task hierarchy quickly instead of experimenting with flat designs.
- **Algorithm selection** — I asked why a greedy approach might fail for this problem and what alternatives existed. The AI explained 0/1 knapsack DP clearly and helped me understand how to adapt the weight to include buffer time per task, which was a non-obvious detail.
- **Debugging** — when the multi-pet schedule always showed conflicts, I described the symptom ("every pet starts at minute 0") and asked what the root cause might be. The AI pointed directly to `get_time_slots()` starting `current = 0` instead of using a staggered offset.
- **Code review** — I pasted individual methods and asked whether edge cases (empty task lists, required tasks exceeding budget, unknown species) were handled correctly.

The most useful prompts were specific and included the actual code or error message. Vague prompts like "make it better" were not helpful. Questions like "what happens if required tasks alone exceed available_minutes?" produced concrete, usable answers.

**b. Judgment and verification**

When implementing conflict detection, the AI initially suggested raising an exception if any plan was `None`. I rejected that because the function is called inside a Streamlit app where a crash would wipe out the user's session. I kept the error path as a warning string returned in the list instead, so the caller always receives a plain `list[str]` regardless of what went wrong. I verified this by manually passing `None` as one of the plans and confirming the app displayed a warning rather than crashing.


**How separate chat sessions for different phases helped:**

I kept separate chat sessions for design, algorithm implementation, and debugging. Starting a new session for each phase meant I was not carrying stale context. When I switched from "how should I structure the classes?" to "why is the knapsack selecting the wrong tasks?", a fresh session gave answers grounded in the actual problem rather than assumptions left over from earlier conversation. It also forced me to re-articulate the problem in my own words each time, which often clarified my thinking before the AI even responded.

**Being the "lead architect" when collaborating with AI:**

The clearest lesson was that AI suggestions are proposals, not decisions. Claude and the chat panel were fast and often correct, but they have no stake in the design. They will suggest a workable solution without knowing which tradeoffs matter to you. I had to stay in the lead by evaluating every suggestion against the constraints I had already set: no crashes in the UI, no greedy shortcuts where correctness mattered, no added complexity that the project did not need. The times I drifted into accepting suggestions passively were the times I had to go back and undo them. The best workflow was to decide what I wanted first, then use AI to help me build it, not to let AI decide and follow along.

---

## 4. Testing and Verification

**a. What you tested**

I tested the following behaviors:

- **Task sorting** — after calling `add_task`, the task list is always sorted by `duration_minutes` shortest-first. This matters because the knapsack iterates the list and the sort order affects which items are backtracked first.
- **Required tasks always appear** — even when required tasks alone exceed `available_minutes`, they are all included and optional tasks are dropped entirely. This is a safety guarantee for critical care items like feeding or medication.
- **Knapsack optimality** — given a budget where a greedy approach would pick one large high-priority task, the knapsack correctly picks two smaller medium-priority tasks when their combined value is higher. This was the key correctness test for the algorithm.
- **Species filtering** — a dog-only task does not appear in a cat's plan, and the explanation correctly reports it as excluded rather than skipped.
- **Conflict detection** — two plans with overlapping time slots return warning strings; tasks that share an endpoint (one ends exactly when the next begins) are not flagged as conflicts because the intervals are half-open.
- **Buffer accounting** — `total_minutes_used` includes buffer gaps between tasks, and a plan with one task has no buffer added.
- **Recurring tasks** — calling `complete_task` on a daily task produces a new pending task with `due_date` advanced by one day; completing a one-time task returns `None`.

These tests mattered because the scheduling logic has no visual output to catch mistakes. If the knapsack selects the wrong tasks silently, the user would never know without a unit test checking the selected set directly.

**b. Confidence**

I am confident the scheduler handles the common cases correctly: single pet, multiple pets, required tasks, species filtering, and buffer time. My confidence is lower for edge cases involving very tight budgets where required tasks slightly exceed capacity, or where all tasks are the same priority and duration (the knapsack tie-breaking behavior depends on iteration order in that case). If I had more time, I would test:

- An owner with one available minute and a required task of five minutes. The plan should still include the required task even though it busts the budget.
- Two pets where one has zero tasks. The proportional allocation should give all time to the pet with tasks.
- A pet whose tasks are all species-ineligible. The plan should produce an empty schedule with a clear explanation rather than an error.

---

## 5. Reflection

**a. What went well**

I am most satisfied with the knapsack scheduling algorithm. Replacing the greedy approach with 0/1 DP was the hardest technical decision in the project, but it made the scheduler genuinely correct instead of just approximately correct. The buffer accounting inside the DP weight (`duration + buffer_minutes` per task) was a subtle detail that took some thought to get right, and seeing it produce better plans than the greedy version in side-by-side tests was rewarding.

I am also happy with how the `Plan` class became self-contained over time. Adding `owner` and `pet` directly to `Plan` meant the UI and test code never had to thread those values through separately, which made every call site cleaner.

**b. What you would improve**

If I had another iteration, I would redesign the multi-pet scheduling to produce a single truly joint timeline instead of staggering independently-optimized plans. The current fix avoids false conflicts by sequencing pets one after another, but each pet's plan is still optimized in isolation. A shared timeline where the owner's time budget is one continuous sequence would allow the scheduler to interleave tasks across pets (e.g. feed the cat while the dog cools down from a walk), which is closer to how care actually works.

I would also add a way to set a specific start time for the day's schedule (e.g. "I have time starting at 8:00 AM") so the time slots display as real clock times rather than abstract minute offsets.

**c. Key takeaway**

The most important thing I learned is that AI tools are most useful when you give them a specific, constrained question and not an open-ended one. Asking "how does 0/1 knapsack work with variable weights?" produced a clean, usable explanation. Asking "make the scheduler better" produced suggestions that did not fit the project's constraints at all. Treating AI like a knowledgeable collaborator who needs context to help, rather than an oracle who already knows what you want, made the collaboration much more productive and kept me in control of the design decisions.
