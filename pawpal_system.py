"""PawPal+ pet care planning system.

Data-holding objects (Owner, Pet, Task) use dataclasses. Scheduler retrieves and
organizes tasks across pets and produces a daily plan.
"""

from dataclasses import dataclass, field
from datetime import date, time
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
