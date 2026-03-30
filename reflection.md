# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The initial UML design models the main concepts from the scenario: who is planning (owner), what is being cared for (pet), what needs to be done (tasks), and how a plan is produced (scheduler). Four classes were chosen so that data (owner, pet, tasks) is separate from the logic that builds the daily plan (scheduler).

**Classes and responsibilities**

- **Owner** — Holds basic owner info: name, available time window (start/end), and preferences. Responsibilities: expose how many minutes are available (`get_available_minutes`), check if a given time is within the window (`is_available`), and return constraints for the scheduler (`get_constraints`).
- **Pet** — Holds the pet's id (stable identifier), name, and species. Responsibilities: provide a string representation (`__str__`) and optional care notes (`get_care_notes`). The care plan is for this pet. Task.pet_id references Pet.id when a task is for a specific pet.
- **Task** — Represents a single care activity (e.g. walk, feeding, meds). Holds id, name, task type, duration, priority, optional preferred time, and optional pet_id (references Pet.id). Responsibilities: return duration (`get_duration_minutes`) and serialize for storage or UI (`to_dict`). Tasks can be added, edited, or removed by the app.
- **Scheduler** — No stored data; it's the behavior class. Responsibilities: take the list of tasks and the owner (for constraints) and produce a daily plan as an ordered list of scheduled items (`generate_plan`), using internal helpers to sort by priority and fit tasks into time windows. It can also explain why the plan was built that way (`explain_plan`).

**Relationships:** Owner has one or more Pets; Owner has many Tasks; Task optionally references one Pet via pet_id (Task.pet_id = Pet.id); Scheduler uses Task, Owner, and optionally Pet to produce the plan output (a list of scheduled items).

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. Several changes were made to encode missing relationships and avoid logic ambiguity:

1. **Owner now holds `pets` and `tasks`** — The UML said "Owner has one or more Pets" and "Owner has many Tasks," but the code didn't model that; the caller held those lists. We added `pets: list[Pet]` and `tasks: list[Task]` to `Owner` (with `default_factory=list`) so the relationship lives in the domain model. The app can still pass a task list into the scheduler (e.g. `owner.tasks` or a filtered list).

2. **Task now has optional `pet_id`** — Tasks weren't linked to a pet, so with multiple pets we couldn't say which pet a task is for. We added `pet_id: str | None = None` to `Task` so tasks can be associated with a pet when needed; scheduling or the UI can use this for pet-specific plans.

3. **Scheduler.generate_plan now accepts optional `pet`** — The scheduler had no way to use pet info (e.g. species or care notes). We added an optional `pet: Pet | None = None` parameter so the scheduler can do pet-aware scheduling when provided, without breaking the existing API when omitted.

4. **Priority constants (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW)** — Priority was an unspecified integer, so sort order (ascending vs descending) was ambiguous. We added module-level constants and documented that lower number means higher priority, so `_sort_by_priority` and any UI use a single, clear convention.

5. **Pet now has `id`; Task–Pet relationship explicit in diagram** — Pet had no identifier, so Task.pet_id had no clear target and the relationship was one-sided. We added `id: str` to Pet so every pet has a stable id and Task.pet_id references it. The class diagram was updated to show Pet.id and the relationship "Task pet_id → Pet" so the link is visible.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three constraints: (1) the owner's available time window (tasks must fit between `available_start` and `available_end`), (2) task priority (high-priority tasks are scheduled first so they are guaranteed a slot), and (3) task duration (the scheduler packs tasks sequentially and stops when the window is full). Priority was chosen as the primary sort key because a missed medication is more critical than a missed play session. Time window enforcement prevents the app from suggesting tasks at 3 AM. Preferred time is used for sorting/display but does not override the greedy priority-first packing — a deliberate choice to keep the algorithm simple while still respecting the owner's most important constraints.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The conflict detection algorithm only checks for exact time-range overlaps between scheduled items rather than considering buffer time between tasks (e.g., travel time between locations) or partial overlaps due to tasks running over their estimated duration. This is a reasonable tradeoff because PawPal+ is a personal pet care planner, not a hospital scheduling system — tasks happen at home with minimal transition time. Checking exact overlaps keeps the logic simple and fast (O(n^2) pairwise comparison, which is fine for the small number of daily pet tasks) while still catching the most common scheduling mistake: accidentally booking two things at the same time. If the app needed to handle dozens of pets or account for travel, a more sophisticated interval-tree approach would be warranted.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

AI (Claude Code) was used across every phase of the project:

- **Design brainstorming** — Asked AI to review the initial UML and suggest missing relationships (e.g., Pet.id as a stable identifier, Task.pet_id foreign key). This caught gaps before any code was written.
- **Implementation** — Gave AI the full phase requirements and let it implement sorting, filtering, recurring tasks, and conflict detection in one pass. The most helpful prompts were specific ("implement `sort_by_time()` using `sorted()` with a lambda key") rather than vague ("make it better").
- **Test generation** — Asked AI to write a comprehensive test suite covering happy paths and edge cases (empty lists, unknown pets, one-time vs. recurring tasks). The prompt "write tests for all new Scheduler methods including edge cases" produced a well-organized 20-test suite.
- **UI integration** — Asked AI to update `app.py` to use `st.table`, `st.warning`, and `st.success` to surface the algorithmic features visually.

Prompts that described the *desired behavior* ("when a daily task is marked complete, auto-create the next occurrence") worked better than prompts that described the *implementation* ("use a for loop to...").

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When implementing `mark_task_complete`, the initial approach stored a `due_date` on each Task and incremented it with `timedelta`. However, the existing Task dataclass had no `due_date` field — only `preferred_time` (a `time`, not a `datetime`). Adding a `due_date` field would have required changes across the serialization (`to_dict`), the UI, and the test fixtures. Instead, the simpler approach was kept: the new recurring task copies the same `preferred_time` and resets `completion_status` to False, leaving date tracking to the caller or a future iteration. This was verified by running the test suite and confirming the recurring task tests passed without modifying the Task schema.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The test suite (20 tests) covers six areas:

1. **Task basics** — `mark_complete()` flips status; adding tasks increases pet count. These verify the foundational data model.
2. **Sorting by time** — Tasks return in chronological order; tasks without a preferred time sort last; empty lists return empty. Sorting is the most visible feature in the UI, so correctness here prevents confusing displays.
3. **Filtering** — By completion status and by pet name, including edge cases (unknown pet name returns empty, no tasks returns empty). Filtering bugs would show the wrong tasks to the user.
4. **Recurring tasks** — Daily and weekly tasks auto-create the next occurrence; one-time tasks do not recur. A bug here would silently lose recurring tasks or create phantom tasks.
5. **Conflict detection** — Exact overlap, partial overlap, adjacent (no conflict), and empty schedule. False positives would annoy users; false negatives would let double-bookings slip through.
6. **Schedule generation** — Pet with no tasks produces empty schedule; tasks exceeding the time window are skipped; high-priority tasks come before low-priority. These are the core scheduler invariants.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**Confidence: 4/5 stars.** All 20 tests pass, covering both happy paths and key edge cases. The scheduler correctly prioritizes, fits tasks into windows, and handles the algorithmic features.

Edge cases to test next:
- Tasks with zero duration
- Owner with a zero-minute availability window (start == end)
- Very large number of tasks (performance)
- Multiple pets with tasks at identical times (cross-pet conflict detection in the generated plan)
- Marking the same task complete twice (idempotency)

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The clean separation between data classes (`Owner`, `Pet`, `Task`) and behavior (`Scheduler`) made it easy to add new algorithmic features without touching the data model. Adding `sort_by_time`, `filter_by_pet`, `detect_conflicts`, and `mark_task_complete` all happened as new methods on `Scheduler` — no existing code had to change. The test suite also came together quickly because each method has a clear input/output contract.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

1. **Date-aware scheduling** — Currently tasks only have a `preferred_time` (time of day) with no date. Adding a `due_date` field would enable multi-day planning, proper recurring task date tracking, and calendar views.
2. **Preferred time as a constraint, not just display** — The scheduler currently ignores `preferred_time` when packing tasks (it sorts by priority and fills sequentially). Ideally it would try to honor preferred times while still respecting priority.
3. **Richer conflict detection** — Check for conflicts across pets (e.g., can the owner really walk the dog and groom the cat at the same time?) and consider buffer time between tasks.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

AI is most effective when you act as the architect and let AI handle implementation. When I described the *what* and *why* clearly (e.g., "detect overlapping time ranges and return warnings"), AI produced clean, correct code on the first try. When I was vague, the suggestions needed more editing. The lesson: invest time in clear requirements and design decisions upfront — AI amplifies the quality of your thinking, for better or worse.

---

## 6. Prompt Comparison: Claude vs. GPT-4 (Challenge 5)

**Task:** Implement logic so that when a recurring (daily/weekly) task is marked complete, a new task instance is automatically created for the next occurrence.

**Prompt given to both models:** *"In my PawPal+ scheduler, I have a Task dataclass with a `frequency` field ('daily', 'weekly', 'once'). When `mark_task_complete` is called on a daily or weekly task, I want the system to automatically create the next occurrence. The Task has `preferred_time` (a `datetime.time`, not a date). Write a `mark_task_complete` method on the Scheduler class."*

### Claude's approach

Claude produced a method that:
1. Calls `task.mark_complete()` to flip the status
2. Checks `task.frequency in ("daily", "weekly")`
3. Creates a new `Task` with the same attributes but `completion_status=False` and `id=f"{task.id}_next"`
4. Appends the new task to the `all_tasks` list passed as a parameter
5. Returns the new task (or `None` for one-time tasks)

**Style:** Minimal and pragmatic. It avoids adding a `due_date` field that doesn't exist on the dataclass, keeping the change self-contained. The `timedelta` import is present but the delta is computed without being applied to a date (since Task has no date field) — this was an honest reflection of the existing schema's limitation.

### GPT-4's approach

GPT-4 produced a method that:
1. Added a `due_date: date | None = None` field to the Task dataclass
2. Used `datetime.combine(task.due_date, task.preferred_time) + timedelta(days=...)` to compute the next occurrence
3. Set the new task's `due_date` to the computed next date
4. Returned a tuple `(completed_task, new_task)` instead of just the new task

**Style:** More complete in the "ideal" sense — it models dates properly. But it required modifying the Task dataclass, which would cascade into `to_dict()`, `load_from_json()`, every test fixture, and the UI. The tuple return type also broke the simple "returns Task | None" contract.

### Verdict

**Claude's version was kept.** It was more *modular* — it worked within the existing schema without forcing changes across the codebase. GPT-4's version was more *correct* in an idealized design, but the cost of adopting it (touching 5+ files, updating all tests) outweighed the benefit for a pet care app where date tracking is not yet critical. The key lesson: the "better" algorithm is the one that fits the current architecture, not the one that's theoretically more complete. When the system grows to need multi-day planning, GPT-4's `due_date` approach would be the right refactor — but premature complexity is a real cost.
