"""Temporary testing ground: run with python main.py to verify PawPal+ logic."""

from datetime import date, time

from pawpal_system import Owner, Pet, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW, Scheduler, Task


def main() -> None:
    # Owner: available 8:00-18:00
    owner = Owner(
        name="Alex",
        available_start=time(8, 0),
        available_end=time(18, 0),
        preferences="Morning walks preferred.",
    )

    # Pet 1: Buddy (dog)
    pet1 = Pet(id="pet1", name="Buddy", species="dog", care_notes="Likes long walks.")
    # Add tasks OUT OF ORDER to test sorting
    pet1.tasks.append(
        Task(
            id="t2",
            name="Feed breakfast",
            description="Morning meal",
            task_type="feeding",
            duration_minutes=15,
            priority=PRIORITY_HIGH,
            preferred_time=time(9, 0),
            pet_id="pet1",
            frequency="daily",
        )
    )
    pet1.tasks.append(
        Task(
            id="t1",
            name="Morning walk",
            description="30 min walk around the block",
            task_type="walk",
            duration_minutes=30,
            priority=PRIORITY_HIGH,
            preferred_time=time(8, 30),
            pet_id="pet1",
            frequency="daily",
        )
    )

    # Pet 2: Whiskers (cat)
    pet2 = Pet(id="pet2", name="Whiskers", species="cat", care_notes="Indoor only.")
    pet2.tasks.append(
        Task(
            id="t3",
            name="Evening play",
            description="15 min enrichment",
            task_type="enrichment",
            duration_minutes=15,
            priority=PRIORITY_MEDIUM,
            preferred_time=time(17, 0),
            pet_id="pet2",
        )
    )
    # Intentional conflict: schedule grooming at the SAME time as evening play
    pet2.tasks.append(
        Task(
            id="t4",
            name="Grooming session",
            description="Brush fur",
            task_type="grooming",
            duration_minutes=20,
            priority=PRIORITY_LOW,
            preferred_time=time(17, 0),
            pet_id="pet2",
        )
    )

    owner.pets = [pet1, pet2]
    all_tasks = owner.get_all_tasks()
    scheduler = Scheduler()
    today = date.today()

    # --- 1. Sort by time ---
    print("=" * 50)
    print("Tasks sorted by preferred time")
    print("=" * 50)
    sorted_tasks = scheduler.sort_by_time(all_tasks)
    for t in sorted_tasks:
        ptime = t.preferred_time.strftime("%H:%M") if t.preferred_time else "None"
        print(f"  {ptime}  {t.name} (pet_id={t.pet_id})")

    # --- 2. Filter by pet ---
    print()
    print("=" * 50)
    print("Tasks for Buddy only")
    print("=" * 50)
    buddy_tasks = scheduler.filter_by_pet(all_tasks, "Buddy", owner.pets)
    for t in buddy_tasks:
        print(f"  {t.name}")

    # --- 3. Filter by completion status ---
    print()
    print("=" * 50)
    print("Incomplete tasks (before completing any)")
    print("=" * 50)
    incomplete = scheduler.filter_by_status(all_tasks, completed=False)
    print(f"  {len(incomplete)} incomplete task(s)")

    # --- 4. Recurring task: mark complete and auto-create next ---
    print()
    print("=" * 50)
    print("Recurring tasks demo")
    print("=" * 50)
    walk_task = next(t for t in all_tasks if t.name == "Morning walk")
    print(f"  Completing '{walk_task.name}' (frequency={walk_task.frequency})...")
    new_task = scheduler.mark_task_complete(walk_task, all_tasks)
    if new_task:
        print(f"  Auto-created next occurrence: id={new_task.id}, completed={new_task.completion_status}")
    completed = scheduler.filter_by_status(all_tasks, completed=True)
    incomplete = scheduler.filter_by_status(all_tasks, completed=False)
    print(f"  Completed: {len(completed)}, Incomplete: {len(incomplete)}")

    # --- 5. Generate schedule and detect conflicts ---
    print()
    print("=" * 50)
    print("Today's Schedule")
    print("=" * 50)
    schedule = scheduler.generate_plan(None, owner, today)
    print(f"Date: {today.strftime('%A, %B %d, %Y')}\n")
    if not schedule:
        print("No tasks scheduled.")
    else:
        for item in schedule:
            t = item["task"]
            start = item["start_time"]
            end = item["end_time"]
            print(f"  {start.strftime('%H:%M')} - {end.strftime('%H:%M')}  {t.name} ({t.task_type})")
            print(f"      {t.description}")
        print()
        print("Why this plan:")
        print(f"  {scheduler.explain_plan(schedule)}")

    # --- 6. Conflict detection with manually-placed tasks ---
    print()
    print("=" * 50)
    print("Conflict Detection")
    print("=" * 50)
    # Simulate two tasks placed at the same 17:00-17:15/17:20 slot
    conflict_items = [
        {"task": pet2.tasks[0], "start_time": time(17, 0), "end_time": time(17, 15)},
        {"task": pet2.tasks[1], "start_time": time(17, 0), "end_time": time(17, 20)},
    ]
    warnings = scheduler.detect_conflicts(conflict_items)
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")
    else:
        print("  No conflicts detected.")
    print("=" * 50)


if __name__ == "__main__":
    main()
