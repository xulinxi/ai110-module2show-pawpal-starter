# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The initial UML design models the main concepts from the scenario: who is planning (owner), what is being cared for (pet), what needs to be done (tasks), and how a plan is produced (scheduler). Four classes were chosen so that data (owner, pet, tasks) is separate from the logic that builds the daily plan (scheduler).

**Classes and responsibilities**

- **Owner** — Holds basic owner info: name, available time window (start/end), and preferences. Responsibilities: expose how many minutes are available (`get_available_minutes`), check if a given time is within the window (`is_available`), and return constraints for the scheduler (`get_constraints`).
- **Pet** — Holds the pet’s id (stable identifier), name, and species. Responsibilities: provide a string representation (`__str__`) and optional care notes (`get_care_notes`). The care plan is for this pet. Task.pet_id references Pet.id when a task is for a specific pet.
- **Task** — Represents a single care activity (e.g. walk, feeding, meds). Holds id, name, task type, duration, priority, optional preferred time, and optional pet_id (references Pet.id). Responsibilities: return duration (`get_duration_minutes`) and serialize for storage or UI (`to_dict`). Tasks can be added, edited, or removed by the app.
- **Scheduler** — No stored data; it’s the behavior class. Responsibilities: take the list of tasks and the owner (for constraints) and produce a daily plan as an ordered list of scheduled items (`generate_plan`), using internal helpers to sort by priority and fit tasks into time windows. It can also explain why the plan was built that way (`explain_plan`).

**Relationships:** Owner has one or more Pets; Owner has many Tasks; Task optionally references one Pet via pet_id (Task.pet_id = Pet.id); Scheduler uses Task, Owner, and optionally Pet to produce the plan output (a list of scheduled items).

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. Several changes were made to encode missing relationships and avoid logic ambiguity:

1. **Owner now holds `pets` and `tasks`** — The UML said "Owner has one or more Pets" and "Owner has many Tasks," but the code didn’t model that; the caller held those lists. We added `pets: list[Pet]` and `tasks: list[Task]` to `Owner` (with `default_factory=list`) so the relationship lives in the domain model. The app can still pass a task list into the scheduler (e.g. `owner.tasks` or a filtered list).

2. **Task now has optional `pet_id`** — Tasks weren’t linked to a pet, so with multiple pets we couldn’t say which pet a task is for. We added `pet_id: str | None = None` to `Task` so tasks can be associated with a pet when needed; scheduling or the UI can use this for pet-specific plans.

3. **Scheduler.generate_plan now accepts optional `pet`** — The scheduler had no way to use pet info (e.g. species or care notes). We added an optional `pet: Pet | None = None` parameter so the scheduler can do pet-aware scheduling when provided, without breaking the existing API when omitted.

4. **Priority constants (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW)** — Priority was an unspecified integer, so sort order (ascending vs descending) was ambiguous. We added module-level constants and documented that lower number means higher priority, so `_sort_by_priority` and any UI use a single, clear convention.

5. **Pet now has `id`; Task–Pet relationship explicit in diagram** — Pet had no identifier, so Task.pet_id had no clear target and the relationship was one-sided. We added `id: str` to Pet so every pet has a stable id and Task.pet_id references it. The class diagram was updated to show Pet.id and the relationship "Task pet_id → Pet" so the link is visible.

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
