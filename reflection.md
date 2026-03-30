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
   In the original skeleton, the scheduler sorted tasks by priority and duration, then greedily added tasks one by one until time ran out. This was simple but produced suboptimal plans — a single long high-priority task could block several shorter tasks that together would be more valuable. I replaced it with a dynamic programming knapsack algorithm that considers all combinations and selects the set of tasks with the highest total priority value that still fits within the available time. This was a more complex implementation but produces genuinely better schedules.

2. The Task class gained a species field.  
   The original Task had no awareness of which pet it applied to. I added an optional species field so that tasks like "walk the dog" could be marked as dog-only and automatically excluded when the pet is a cat. The Scheduler now filters tasks by species eligibility before scheduling, and the explanation separately reports tasks excluded for species mismatch versus tasks skipped due to time.

3. The Plan class gained owner and pet fields.  
   In the skeleton, Plan only stored selected_tasks, total_minutes_used, and explanation. The final implementation added owner and pet so that the plan is self-contained — it carries all the context needed to display or summarize the result without passing the owner and pet separately to the UI.

4. Input validation was added to Owner, Pet, and Task.  
   The initial skeletons were plain dataclasses with no validation. I added **post_init** methods to enforce that available_minutes and duration_minutes are positive, that priority is one of {"high", "medium", "low"}, and that species is one of {"dog", "cat", "other"}. This prevents silent bugs caused by bad input reaching the scheduler.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**. 

**Tradeoff: Conflict detection is reactive, not preventive.**

The scheduler creates each pet's plan separately, giving each pet its fair share of the owner's available time. After that, it checks the schedules for any overlapping tasks. If it finds overlaps, it just reports a warning—it doesn't try to fix the problem by rescheduling anything.

This approach makes sense for a daily pet care planner because most people have just one pet, and in that case, there can't be any conflicts within a single pet's schedule by design. For households with multiple pets, the way time is divided proportionally already helps avoid overlaps without needing a complicated joint scheduling system. Using reactive detection keeps each pet's plan straightforward and optimized individually, while still letting the user know about any issues. Trying to prevent conflicts upfront by finding a perfect schedule for all pets at once would be way too complex and unnecessary for a typical home with a couple of pets whose care doesn't need to be coordinated down to the minute.  

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
