"""PawPal+ pet care planning system.

Data-holding objects (Owner, Pet, Task) use dataclasses. Scheduler retrieves and
organizes tasks across pets and produces a daily plan.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from pathlib import Path
from typing import Any

# Priority: lower number = higher priority.
PRIORITY_HIGH = 1
PRIORITY_MEDIUM = 2
PRIORITY_LOW = 3


@dataclass
class Task:
    """A single activity: description, time, frequency, completion status."""

    id: str
    name: str
    description: str
    task_type: str
    duration_minutes: int
    priority: int
    preferred_time: time | None = None
    pet_id: str | None = None
    frequency: str = "daily"
    completion_status: bool = False

    def get_duration_minutes(self) -> int:
        """Return duration in minutes."""
        return self.duration_minutes

    def mark_complete(self) -> None:
        """Set completion status to True."""
        self.completion_status = True

    def to_dict(self) -> dict[str, Any]:
        """Return a dict of all fields for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "preferred_time": self.preferred_time.isoformat() if self.preferred_time else None,
            "pet_id": self.pet_id,
            "frequency": self.frequency,
            "completion_status": self.completion_status,
        }


@dataclass
class Pet:
    """Stores pet details and a list of tasks."""

    id: str
    name: str
    species: str
    care_notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def __str__(self) -> str:
        """Return 'Name (species)'."""
        return f"{self.name} ({self.species})"

    def get_care_notes(self) -> str:
        """Return this pet's care notes."""
        return self.care_notes


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    name: str
    available_start: time
    available_end: time
    preferences: str = ""
    pets: list[Pet] = field(default_factory=list)

    def get_all_tasks(self) -> list[Task]:
        """Return tasks from all pets."""
        return [t for pet in self.pets for t in pet.tasks]

    def get_available_minutes(self) -> int:
        """Return available minutes between start and end time."""
        start_m = self.available_start.hour * 60 + self.available_start.minute
        end_m = self.available_end.hour * 60 + self.available_end.minute
        return max(0, end_m - start_m)

    def is_available(self, at_time: time) -> bool:
        """Return True if at_time is within the owner's available window."""
        t_m = at_time.hour * 60 + at_time.minute
        start_m = self.available_start.hour * 60 + self.available_start.minute
        end_m = self.available_end.hour * 60 + self.available_end.minute
        return start_m <= t_m < end_m

    def get_constraints(self) -> dict[str, Any]:
        """Return time window and preferences for the scheduler."""
        return {
            "available_start": self.available_start,
            "available_end": self.available_end,
            "available_minutes": self.get_available_minutes(),
            "preferences": self.preferences,
        }

    # --- JSON persistence (Challenge 2) -------------------------------------

    def save_to_json(self, path: str | Path = "data.json") -> None:
        """Serialize owner, pets, and all tasks to a JSON file."""
        data = {
            "name": self.name,
            "available_start": self.available_start.isoformat(),
            "available_end": self.available_end.isoformat(),
            "preferences": self.preferences,
            "pets": [
                {
                    "id": pet.id,
                    "name": pet.name,
                    "species": pet.species,
                    "care_notes": pet.care_notes,
                    "tasks": [t.to_dict() for t in pet.tasks],
                }
                for pet in self.pets
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load_from_json(cls, path: str | Path = "data.json") -> Owner:
        """Deserialize an Owner (with pets and tasks) from a JSON file."""
        raw = json.loads(Path(path).read_text())
        pets: list[Pet] = []
        for p in raw.get("pets", []):
            tasks = [
                Task(
                    id=t["id"],
                    name=t["name"],
                    description=t["description"],
                    task_type=t["task_type"],
                    duration_minutes=t["duration_minutes"],
                    priority=t["priority"],
                    preferred_time=time.fromisoformat(t["preferred_time"]) if t.get("preferred_time") else None,
                    pet_id=t.get("pet_id"),
                    frequency=t.get("frequency", "daily"),
                    completion_status=t.get("completion_status", False),
                )
                for t in p.get("tasks", [])
            ]
            pets.append(Pet(id=p["id"], name=p["name"], species=p["species"],
                           care_notes=p.get("care_notes", ""), tasks=tasks))
        return cls(
            name=raw["name"],
            available_start=time.fromisoformat(raw["available_start"]),
            available_end=time.fromisoformat(raw["available_end"]),
            preferences=raw.get("preferences", ""),
            pets=pets,
        )


class Scheduler:
    """Retrieves, organizes, and manages tasks across pets; produces a daily plan."""

    def generate_plan(
        self,
        tasks: list[Task] | None,
        owner: Owner,
        plan_date: date,
        pet: Pet | None = None,
    ) -> list[dict[str, Any]]:
        """Return scheduled items (task + start/end time); uses owner's tasks if none provided."""
        tasks_to_plan = tasks if tasks is not None and len(tasks) > 0 else owner.get_all_tasks()
        if pet is not None:
            tasks_to_plan = [t for t in tasks_to_plan if t.pet_id is None or t.pet_id == pet.id]
        tasks_to_plan = self._sort_by_priority(tasks_to_plan)
        constraints = owner.get_constraints()
        start = constraints["available_start"]
        end = constraints["available_end"]
        return self._fit_into_windows(tasks_to_plan, start, end)

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority ascending (lower number first)."""
        return sorted(tasks, key=lambda t: t.priority)

    def _fit_into_windows(
        self,
        tasks: list[Task],
        start: time,
        end: time,
    ) -> list[dict[str, Any]]:
        """Place tasks back-to-back in [start, end]; returns list of {task, start_time, end_time}."""
        result: list[dict[str, Any]] = []
        start_min = start.hour * 60 + start.minute
        end_min = end.hour * 60 + end.minute
        current_min = start_min
        for task in tasks:
            duration = task.get_duration_minutes()
            if current_min + duration > end_min:
                break
            start_time = time(current_min // 60, current_min % 60)
            current_min += duration
            end_time = time(current_min // 60, current_min % 60)
            result.append({
                "task": task,
                "start_time": start_time,
                "end_time": end_time,
            })
        return result

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by their preferred_time (earliest first). Tasks without a time go last."""
        return sorted(tasks, key=lambda t: (t.preferred_time is None, t.preferred_time or time(23, 59)))

    def filter_by_status(self, tasks: list[Task], completed: bool) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in tasks if t.completion_status == completed]

    def filter_by_pet(self, tasks: list[Task], pet_name: str, pets: list[Pet]) -> list[Task]:
        """Return tasks belonging to the pet with the given name."""
        pet_ids = {p.id for p in pets if p.name == pet_name}
        return [t for t in tasks if t.pet_id in pet_ids]

    def mark_task_complete(self, task: Task, all_tasks: list[Task]) -> Task | None:
        """Mark a task complete. If it recurs (daily/weekly), create and return the next occurrence."""
        task.mark_complete()
        if task.frequency in ("daily", "weekly"):
            delta = timedelta(days=1) if task.frequency == "daily" else timedelta(days=7)
            next_time = task.preferred_time  # time-of-day stays the same
            new_task = Task(
                id=f"{task.id}_next",
                name=task.name,
                description=task.description,
                task_type=task.task_type,
                duration_minutes=task.duration_minutes,
                priority=task.priority,
                preferred_time=next_time,
                pet_id=task.pet_id,
                frequency=task.frequency,
                completion_status=False,
            )
            all_tasks.append(new_task)
            return new_task
        return None

    def detect_conflicts(self, scheduled_items: list[dict[str, Any]]) -> list[str]:
        """Return warning messages for any tasks that overlap in time."""
        warnings: list[str] = []
        for i, a in enumerate(scheduled_items):
            for b in scheduled_items[i + 1:]:
                # Two items conflict if their time ranges overlap
                if a["start_time"] < b["end_time"] and b["start_time"] < a["end_time"]:
                    warnings.append(
                        f"Conflict: '{a['task'].name}' ({a['start_time'].strftime('%H:%M')}-"
                        f"{a['end_time'].strftime('%H:%M')}) overlaps with "
                        f"'{b['task'].name}' ({b['start_time'].strftime('%H:%M')}-"
                        f"{b['end_time'].strftime('%H:%M')})"
                    )
        return warnings

    def find_next_available_slot(
        self,
        scheduled_items: list[dict[str, Any]],
        duration_minutes: int,
        owner: Owner,
    ) -> time | None:
        """Find the earliest slot of `duration_minutes` that doesn't overlap existing items.

        Returns the start time of the slot, or None if no slot fits in the owner's window.
        """
        start_min = owner.available_start.hour * 60 + owner.available_start.minute
        end_min = owner.available_end.hour * 60 + owner.available_end.minute

        # Collect occupied ranges as (start, end) in minutes, sorted
        occupied = sorted(
            (item["start_time"].hour * 60 + item["start_time"].minute,
             item["end_time"].hour * 60 + item["end_time"].minute)
            for item in scheduled_items
        )

        cursor = start_min
        for occ_start, occ_end in occupied:
            if cursor + duration_minutes <= occ_start:
                return time(cursor // 60, cursor % 60)
            cursor = max(cursor, occ_end)

        # Check gap after all occupied items
        if cursor + duration_minutes <= end_min:
            return time(cursor // 60, cursor % 60)
        return None

    # --- Formatting helpers (Challenge 4) -----------------------------------

    TASK_TYPE_EMOJI: dict[str, str] = {
        "walk": "🚶",
        "feeding": "🍽️",
        "meds": "💊",
        "enrichment": "🧩",
        "grooming": "✂️",
        "general": "📋",
    }

    PRIORITY_EMOJI: dict[int, str] = {
        PRIORITY_HIGH: "🔴",
        PRIORITY_MEDIUM: "🟡",
        PRIORITY_LOW: "🟢",
    }

    def format_task_type(self, task_type: str) -> str:
        """Return task type with its emoji prefix."""
        emoji = self.TASK_TYPE_EMOJI.get(task_type, "📋")
        return f"{emoji} {task_type.capitalize()}"

    def format_priority(self, priority: int) -> str:
        """Return priority label with color-coded emoji."""
        labels = {PRIORITY_HIGH: "High", PRIORITY_MEDIUM: "Medium", PRIORITY_LOW: "Low"}
        emoji = self.PRIORITY_EMOJI.get(priority, "⚪")
        return f"{emoji} {labels.get(priority, str(priority))}"

    def format_status(self, completed: bool) -> str:
        """Return a color-coded status string."""
        return "✅ Done" if completed else "⏳ Pending"

    def explain_plan(self, scheduled_items: list[dict[str, Any]]) -> str:
        """Return a brief explanation of the scheduled plan."""
        if not scheduled_items:
            return "No tasks were scheduled (none provided or none fit in the available time)."
        parts = [f"{len(scheduled_items)} task(s) scheduled in priority order."]
        for item in scheduled_items:
            t = item["task"]
            st = item["start_time"]
            parts.append(f"- {t.name} at {st.strftime('%H:%M')} (priority {t.priority}, {t.duration_minutes} min)")
        return " ".join(parts)
