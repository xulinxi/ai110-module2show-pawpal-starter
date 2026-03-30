"""Tests for PawPal+ core behavior, sorting, filtering, recurrence, conflicts,
next-available-slot, and JSON persistence."""

from datetime import date, time
from pathlib import Path

import pytest

from pawpal_system import (
    Owner,
    Pet,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    Scheduler,
    Task,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(id: str, name: str, preferred_time: time | None = None,
               pet_id: str | None = None, priority: int = PRIORITY_MEDIUM,
               frequency: str = "daily", completed: bool = False) -> Task:
    """Shortcut to build a Task with sensible defaults."""
    t = Task(
        id=id, name=name, description=name, task_type="general",
        duration_minutes=15, priority=priority,
        preferred_time=preferred_time, pet_id=pet_id, frequency=frequency,
    )
    if completed:
        t.mark_complete()
    return t


def _make_owner(*pets: Pet) -> Owner:
    """Create an owner available 08:00–18:00 with the given pets."""
    return Owner(
        name="Alex", available_start=time(8, 0), available_end=time(18, 0),
        pets=list(pets),
    )


# ---------------------------------------------------------------------------
# Existing tests (Phase 2)
# ---------------------------------------------------------------------------

def test_task_completion_mark_complete_changes_status() -> None:
    task = _make_task("t1", "Walk")
    assert task.completion_status is False
    task.mark_complete()
    assert task.completion_status is True


def test_task_addition_increases_pet_task_count() -> None:
    pet = Pet(id="pet1", name="Buddy", species="dog")
    assert len(pet.tasks) == 0
    pet.tasks.append(_make_task("t1", "Feed", pet_id="pet1"))
    assert len(pet.tasks) == 1
    pet.tasks.append(_make_task("t2", "Walk", pet_id="pet1"))
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

class TestSortByTime:
    def test_sorts_tasks_in_chronological_order(self) -> None:
        tasks = [
            _make_task("t1", "Late",  preferred_time=time(17, 0)),
            _make_task("t2", "Early", preferred_time=time(8, 0)),
            _make_task("t3", "Mid",   preferred_time=time(12, 0)),
        ]
        result = Scheduler().sort_by_time(tasks)
        assert [t.name for t in result] == ["Early", "Mid", "Late"]

    def test_tasks_without_time_go_last(self) -> None:
        tasks = [
            _make_task("t1", "No time"),
            _make_task("t2", "Has time", preferred_time=time(9, 0)),
        ]
        result = Scheduler().sort_by_time(tasks)
        assert result[0].name == "Has time"
        assert result[1].name == "No time"

    def test_empty_list_returns_empty(self) -> None:
        assert Scheduler().sort_by_time([]) == []


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

class TestFilterByStatus:
    def test_returns_only_incomplete_tasks(self) -> None:
        tasks = [
            _make_task("t1", "Done", completed=True),
            _make_task("t2", "Pending"),
            _make_task("t3", "Also done", completed=True),
        ]
        result = Scheduler().filter_by_status(tasks, completed=False)
        assert [t.name for t in result] == ["Pending"]

    def test_returns_only_completed_tasks(self) -> None:
        tasks = [
            _make_task("t1", "Done", completed=True),
            _make_task("t2", "Pending"),
        ]
        result = Scheduler().filter_by_status(tasks, completed=True)
        assert [t.name for t in result] == ["Done"]


class TestFilterByPet:
    def test_returns_tasks_for_named_pet(self) -> None:
        pets = [
            Pet(id="p1", name="Buddy", species="dog"),
            Pet(id="p2", name="Whiskers", species="cat"),
        ]
        tasks = [
            _make_task("t1", "Walk", pet_id="p1"),
            _make_task("t2", "Play", pet_id="p2"),
            _make_task("t3", "Feed", pet_id="p1"),
        ]
        result = Scheduler().filter_by_pet(tasks, "Buddy", pets)
        assert [t.name for t in result] == ["Walk", "Feed"]

    def test_unknown_pet_returns_empty(self) -> None:
        pets = [Pet(id="p1", name="Buddy", species="dog")]
        tasks = [_make_task("t1", "Walk", pet_id="p1")]
        assert Scheduler().filter_by_pet(tasks, "Ghost", pets) == []

    def test_pet_with_no_tasks_returns_empty(self) -> None:
        pets = [Pet(id="p1", name="Buddy", species="dog")]
        result = Scheduler().filter_by_pet([], "Buddy", pets)
        assert result == []


# ---------------------------------------------------------------------------
# Recurring tasks
# ---------------------------------------------------------------------------

class TestRecurringTasks:
    def test_daily_task_creates_next_occurrence(self) -> None:
        all_tasks: list[Task] = []
        task = _make_task("t1", "Walk", frequency="daily", preferred_time=time(8, 0))
        all_tasks.append(task)

        new = Scheduler().mark_task_complete(task, all_tasks)

        assert task.completion_status is True
        assert new is not None
        assert new.completion_status is False
        assert new.id == "t1_next"
        assert new.preferred_time == time(8, 0)
        assert len(all_tasks) == 2

    def test_weekly_task_creates_next_occurrence(self) -> None:
        all_tasks: list[Task] = []
        task = _make_task("t1", "Grooming", frequency="weekly")
        all_tasks.append(task)

        new = Scheduler().mark_task_complete(task, all_tasks)

        assert task.completion_status is True
        assert new is not None
        assert new.frequency == "weekly"
        assert len(all_tasks) == 2

    def test_one_time_task_does_not_recur(self) -> None:
        all_tasks: list[Task] = []
        task = _make_task("t1", "Vet visit", frequency="once")
        all_tasks.append(task)

        new = Scheduler().mark_task_complete(task, all_tasks)

        assert task.completion_status is True
        assert new is None
        assert len(all_tasks) == 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

class TestConflictDetection:
    def _item(self, task: Task, start: time, end: time) -> dict:
        return {"task": task, "start_time": start, "end_time": end}

    def test_exact_same_time_is_conflict(self) -> None:
        items = [
            self._item(_make_task("t1", "Play"), time(17, 0), time(17, 15)),
            self._item(_make_task("t2", "Groom"), time(17, 0), time(17, 20)),
        ]
        warnings = Scheduler().detect_conflicts(items)
        assert len(warnings) == 1
        assert "Play" in warnings[0]
        assert "Groom" in warnings[0]

    def test_partial_overlap_is_conflict(self) -> None:
        items = [
            self._item(_make_task("t1", "A"), time(9, 0), time(9, 30)),
            self._item(_make_task("t2", "B"), time(9, 15), time(9, 45)),
        ]
        assert len(Scheduler().detect_conflicts(items)) == 1

    def test_adjacent_tasks_no_conflict(self) -> None:
        items = [
            self._item(_make_task("t1", "A"), time(9, 0), time(9, 30)),
            self._item(_make_task("t2", "B"), time(9, 30), time(10, 0)),
        ]
        assert Scheduler().detect_conflicts(items) == []

    def test_no_tasks_no_conflict(self) -> None:
        assert Scheduler().detect_conflicts([]) == []


# ---------------------------------------------------------------------------
# Schedule generation (edge cases)
# ---------------------------------------------------------------------------

class TestGeneratePlan:
    def test_pet_with_no_tasks_produces_empty_schedule(self) -> None:
        pet = Pet(id="p1", name="Buddy", species="dog")
        owner = _make_owner(pet)
        schedule = Scheduler().generate_plan(None, owner, date.today())
        assert schedule == []

    def test_task_exceeding_window_is_skipped(self) -> None:
        """Owner has only 10 minutes; a 30-min task should not be scheduled."""
        owner = Owner(
            name="Alex", available_start=time(8, 0), available_end=time(8, 10),
            pets=[Pet(id="p1", name="Buddy", species="dog",
                      tasks=[_make_task("t1", "Long walk",
                                        priority=PRIORITY_HIGH,
                                        pet_id="p1")])],
        )
        # Task default is 15 min which exceeds the 10-min window
        schedule = Scheduler().generate_plan(None, owner, date.today())
        assert schedule == []

    def test_high_priority_scheduled_before_low(self) -> None:
        pet = Pet(id="p1", name="Buddy", species="dog", tasks=[
            _make_task("t1", "Low", priority=PRIORITY_LOW, pet_id="p1"),
            _make_task("t2", "High", priority=PRIORITY_HIGH, pet_id="p1"),
        ])
        owner = _make_owner(pet)
        schedule = Scheduler().generate_plan(None, owner, date.today())
        assert schedule[0]["task"].name == "High"
        assert schedule[1]["task"].name == "Low"


# ---------------------------------------------------------------------------
# Next available slot (Challenge 1)
# ---------------------------------------------------------------------------

class TestNextAvailableSlot:
    def _item(self, task: Task, start: time, end: time) -> dict:
        return {"task": task, "start_time": start, "end_time": end}

    def test_finds_gap_between_tasks(self) -> None:
        owner = _make_owner()
        items = [
            self._item(_make_task("t1", "A"), time(8, 0), time(8, 30)),
            self._item(_make_task("t2", "B"), time(9, 0), time(9, 30)),
        ]
        # 30-min gap from 8:30 to 9:00
        slot = Scheduler().find_next_available_slot(items, 30, owner)
        assert slot == time(8, 30)

    def test_finds_slot_after_all_tasks(self) -> None:
        owner = _make_owner()
        items = [
            self._item(_make_task("t1", "A"), time(8, 0), time(8, 30)),
        ]
        slot = Scheduler().find_next_available_slot(items, 15, owner)
        assert slot == time(8, 30)

    def test_returns_none_when_no_slot_fits(self) -> None:
        owner = Owner(name="Alex", available_start=time(8, 0), available_end=time(8, 30))
        items = [
            self._item(_make_task("t1", "A"), time(8, 0), time(8, 30)),
        ]
        assert Scheduler().find_next_available_slot(items, 15, owner) is None

    def test_empty_schedule_returns_window_start(self) -> None:
        owner = _make_owner()
        slot = Scheduler().find_next_available_slot([], 15, owner)
        assert slot == time(8, 0)


# ---------------------------------------------------------------------------
# JSON persistence (Challenge 2)
# ---------------------------------------------------------------------------

class TestJsonPersistence:
    def test_round_trip_save_load(self, tmp_path: Path) -> None:
        pet = Pet(id="p1", name="Buddy", species="dog", care_notes="Good boy",
                  tasks=[_make_task("t1", "Walk", preferred_time=time(9, 0), pet_id="p1")])
        owner = _make_owner(pet)
        owner.preferences = "Morning walks"

        filepath = tmp_path / "data.json"
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)

        assert loaded.name == owner.name
        assert loaded.available_start == owner.available_start
        assert loaded.preferences == "Morning walks"
        assert len(loaded.pets) == 1
        assert loaded.pets[0].name == "Buddy"
        assert loaded.pets[0].care_notes == "Good boy"
        assert len(loaded.pets[0].tasks) == 1
        assert loaded.pets[0].tasks[0].name == "Walk"
        assert loaded.pets[0].tasks[0].preferred_time == time(9, 0)

    def test_empty_owner_round_trip(self, tmp_path: Path) -> None:
        owner = _make_owner()
        filepath = tmp_path / "data.json"
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)
        assert loaded.name == "Alex"
        assert loaded.pets == []


# ---------------------------------------------------------------------------
# Formatting helpers (Challenge 4)
# ---------------------------------------------------------------------------

class TestFormatting:
    def test_format_priority_high(self) -> None:
        result = Scheduler().format_priority(PRIORITY_HIGH)
        assert "🔴" in result
        assert "High" in result

    def test_format_task_type_walk(self) -> None:
        result = Scheduler().format_task_type("walk")
        assert "🚶" in result

    def test_format_status_done(self) -> None:
        assert "✅" in Scheduler().format_status(True)

    def test_format_status_pending(self) -> None:
        assert "⏳" in Scheduler().format_status(False)
