# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The initial UML design models the main concepts from the scenario: who is planning (owner), what is being cared for (pet), what needs to be done (tasks), and how a plan is produced (scheduler).

Classes and responsibilities:

- **Owner** — Holds basic owner info (e.g., name, time available) and owns one or more pets. Responsible for providing constraints the scheduler will use.
- **Pet** — Represents the pet (name, species/type). Linked to an owner; the care plan is for this pet.
- **Task** — Represents a single care activity (e.g., walk, feeding, meds). Has at least duration and priority; may have type, preferred time, or other fields. Can be added, edited, or removed.
- **Scheduler** — Takes the set of tasks plus owner/pet constraints (time available, priorities, preferences) and produces a daily plan (e.g. an ordered list of scheduled items with time slots and optional reasoning). Responsible for ordering and timing tasks and optionally explaining why it chose that plan.

Relationships: Owner has one or more Pets; Owner (or Pet) has many Tasks; Scheduler uses Tasks and constraints to produce the plan output.

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
