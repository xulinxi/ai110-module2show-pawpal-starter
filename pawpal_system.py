"""PawPal+ pet care planning system — class stubs from UML.

Data-holding objects (Owner, Pet, Task) use dataclasses: the decorator generates __init__,
__repr__, and other boilerplate from the declared attributes, keeping the code clean.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any

# Priority: lower number = higher priority (e.g. 1=high, 2=medium, 3=low). Used by Scheduler._sort_by_priority.
PRIORITY_HIGH = 1
PRIORITY_MEDIUM = 2
PRIORITY_LOW = 3


@dataclass
class Owner:
    """Pet owner; holds availability, preferences, and their pets and tasks."""

    name: str
    available_start: time
    available_end: time
    preferences: str = ""
    pets: list["Pet"] = field(default_factory=list)
    tasks: list["Task"] = field(default_factory=list)

    def get_available_minutes(self) -> int:
        """Return total minutes available in the day."""
        pass

    def is_available(self, at_time: time) -> bool:
        """Return whether the given time falls within the owner's available window."""
        pass

    def get_constraints(self) -> dict[str, Any]:
        """Return constraints (time window, preferences) for the scheduler."""
        pass


@dataclass
class Pet:
    """Represents a pet (name, species)."""

    name: str
    species: str

    def __str__(self) -> str:
        """Return a string representation of the pet."""
        pass

    def get_care_notes(self) -> str:
        """Return any care notes for this pet."""
        pass


@dataclass
class Task:
    """A single care activity (e.g. walk, feeding, meds). May be linked to a pet when multiple pets exist."""

    id: str
    name: str
    task_type: str
    duration_minutes: int
    priority: int
    preferred_time: time | None = None
    pet_id: str | None = None

    def get_duration_minutes(self) -> int:
        """Return the task duration in minutes."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Return a dict representation for serialization."""
        pass


class Scheduler:
    """Produces a daily plan from tasks and owner constraints."""

    def generate_plan(
        self,
        tasks: list[Task],
        owner: Owner,
        plan_date: date,
        pet: Pet | None = None,
    ) -> list[Any]:
        """Return an ordered list of scheduled items (task + time slot). Optional pet for pet-aware scheduling."""
        pass

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority (internal helper)."""
        pass

    def _fit_into_windows(
        self,
        tasks: list[Task],
        start: time,
        end: time,
    ) -> list[Any]:
        """Assign start/end times within the given window (internal helper)."""
        pass

    def explain_plan(self, scheduled_items: list[Any]) -> str:
        """Return a short explanation of why the plan was built this way."""
        pass
