# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit-powered pet care planning assistant that helps busy pet owners stay on top of daily care tasks.

## Features

- **Owner & pet management** — Set your availability window and add multiple pets with species and care notes
- **Task scheduling** — Add tasks with duration, priority, preferred time, type, and frequency (daily/weekly/once)
- **Priority-based planning** — The scheduler packs 🔴 High-priority tasks first, then 🟡 Medium, then 🟢 Low, within your available time window
- **Sort by time** — View tasks in chronological order based on preferred time
- **Filter by pet or status** — Quickly isolate tasks for a specific pet or see only ⏳ Pending / ✅ Done items
- **Recurring tasks** — Daily and weekly tasks automatically regenerate when marked complete
- **Conflict detection** — Overlapping tasks trigger ⚠️ warnings so you can resolve double-bookings
- **Next available slot** — After generating a schedule, find the earliest open slot for a new task of any duration
- **Data persistence** — Pets and tasks are saved to `data.json` and restored on next launch
- **Emoji-rich UI** — Task types (🚶 walk, 🍽️ feeding, 💊 meds, 🧩 enrichment, ✂️ grooming) and priorities are color-coded for quick scanning
- **Plan explanation** — The scheduler explains why it built the plan it did

## Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the CLI demo

```bash
python main.py
```

## Smarter Scheduling

PawPal+ includes algorithmic features that make daily pet care planning more intelligent:

- **Sort by time** — Tasks are sorted by their preferred time using `Scheduler.sort_by_time()`, so the daily view always shows the earliest tasks first.
- **Filter by pet or status** — `filter_by_pet()` and `filter_by_status()` let you quickly see only a specific pet's tasks, or only incomplete tasks, without manual searching.
- **Recurring tasks** — When a daily or weekly task is marked complete via `mark_task_complete()`, the system automatically creates the next occurrence using `timedelta`, so owners never have to re-enter routine tasks.
- **Conflict detection** — `detect_conflicts()` scans the schedule for overlapping time ranges and returns human-readable warnings instead of crashing, so the owner can resolve double-bookings.
- **Next available slot** — `find_next_available_slot()` scans gaps between scheduled items and returns the earliest start time that fits a given duration, letting owners quickly find where to add a new task.

## Advanced Features (Challenges)

### Challenge 1: Next Available Slot (Agent Mode)

The `Scheduler.find_next_available_slot()` method was implemented using Agent Mode. The prompt given was: *"Add a method to Scheduler that finds the earliest gap of N minutes in a list of scheduled items, respecting the owner's availability window."* Agent Mode analyzed the existing `_fit_into_windows` pattern, then produced a gap-scanning algorithm that sorts occupied ranges, walks a cursor through the gaps, and returns the first slot that fits. This was integrated into the Streamlit UI as a post-schedule query: after generating a schedule, the user can ask "where does a 15-minute task fit?" and get an instant answer.

### Challenge 2: Data Persistence (JSON)

`Owner.save_to_json()` and `Owner.load_from_json()` serialize the entire object graph (owner, pets, tasks) to `data.json` using Python's built-in `json` module and the existing `Task.to_dict()` method. The Streamlit app loads this file on startup and saves after every mutation (add pet, add task, mark complete). No external libraries like marshmallow were needed — custom dict conversion via dataclass fields was sufficient for this flat schema.

### Challenge 3: Priority-Based Scheduling with Emoji UI

Priority was already the primary sort key in the scheduler (`_sort_by_priority`). The UI enhancement adds color-coded emoji indicators: 🔴 High, 🟡 Medium, 🟢 Low. Task types also get emojis (🚶 walk, 🍽️ feeding, 💊 meds, 🧩 enrichment, ✂️ grooming, 📋 general). These are rendered via `Scheduler.format_priority()` and `Scheduler.format_task_type()` helper methods, keeping formatting logic in the backend so both the Streamlit UI and CLI can use it.

### Challenge 4: Professional UI Formatting

The Streamlit UI uses `st.table` for structured display, `st.warning` for conflict alerts, `st.success` for confirmations, `st.info` for slot suggestions, and `st.toast` for load notifications. Every table cell uses emoji-prefixed labels for task type, priority, and status, making the interface scannable at a glance. The "Find Next Available Slot" widget provides an interactive post-schedule query.

### Challenge 5: Multi-Model Prompt Comparison

See the **Prompt Comparison** section in [`reflection.md`](reflection.md) for a documented comparison of Claude vs. GPT-4 approaches to the recurring-task rescheduling algorithm.

## Testing PawPal+

Run the test suite with:

```bash
python -m pytest
```

The suite includes **20+ tests** covering:

- **Task basics** — marking complete, adding tasks to pets
- **Sorting** — chronological order, tasks without a preferred time sort last, empty list
- **Filtering** — by completion status (done/pending) and by pet name, including edge cases (unknown pet, no tasks)
- **Recurring tasks** — daily and weekly tasks auto-create the next occurrence; one-time tasks do not
- **Conflict detection** — exact overlaps, partial overlaps, adjacent (non-overlapping) tasks, empty schedule
- **Schedule generation** — pet with no tasks, task exceeding the time window, priority ordering
- **Next available slot** — finds gaps, handles full schedules, respects owner window
- **JSON persistence** — round-trip save/load preserves all data

**Confidence Level:** 4/5 stars — all happy paths and key edge cases pass; further iteration would add tests for multi-day plans and overlapping owner availability windows.

## Architecture

See [`class-diagram.md`](class-diagram.md) for the full Mermaid.js UML diagram. The system has four classes:

| Class | Role |
|---|---|
| **Owner** | Holds availability window, preferences, list of pets, and JSON persistence |
| **Pet** | Stores pet info and its associated tasks |
| **Task** | A single care activity with priority, time, duration, type, and frequency |
| **Scheduler** | Stateless engine that sorts, filters, schedules, detects conflicts, finds slots, and formats output |
