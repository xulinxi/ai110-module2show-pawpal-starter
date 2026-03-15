"""Temporary testing ground: run with python main.py to verify PawPal+ logic."""

from datetime import date, time

from pawpal_system import Owner, Pet, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW, Scheduler, Task


def main() -> None:
    # Owner: available 8:00–18:00
    owner = Owner(
        name="Alex",
        available_start=time(8, 0),
        available_end=time(18, 0),
        preferences="Morning walks preferred.",
    )

    # Pet 1: Buddy (dog)
    pet1 = Pet(id="pet1", name="Buddy", species="dog", care_notes="Likes long walks.")
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
        )
    )
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

    owner.pets = [pet1, pet2]

    # Generate today's schedule
    scheduler = Scheduler()
    today = date.today()
    schedule = scheduler.generate_plan(None, owner, today)
    explanation = scheduler.explain_plan(schedule)

    # Print Today's Schedule
    print("=" * 50)
    print("Today's Schedule")
    print("=" * 50)
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
        print(f"  {explanation}")
    print("=" * 50)


if __name__ == "__main__":
    main()
