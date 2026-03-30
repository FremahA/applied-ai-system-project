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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
