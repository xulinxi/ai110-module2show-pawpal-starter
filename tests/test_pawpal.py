"""Quick tests for PawPal+ core behavior."""

import pytest

from pawpal_system import Pet, Task


def test_task_completion_mark_complete_changes_status() -> None:
    """Verify that calling mark_complete() actually changes the task's status."""
    task = Task(
        id="t1",
        name="Morning walk",
        description="Walk the dog",
        task_type="walk",
        duration_minutes=30,
        priority=1,
    )
    assert task.completion_status is False
    task.mark_complete()
    assert task.completion_status is True


def test_task_addition_increases_pet_task_count() -> None:
    """Verify that adding a task to a Pet increases that pet's task count."""
    pet = Pet(id="pet1", name="Buddy", species="dog")
    assert len(pet.tasks) == 0

    task = Task(
        id="t1",
        name="Feed",
        description="Morning meal",
        task_type="feeding",
        duration_minutes=15,
        priority=1,
        pet_id="pet1",
    )
    pet.tasks.append(task)
    assert len(pet.tasks) == 1

    pet.tasks.append(
        Task(
            id="t2",
            name="Walk",
            description="Evening walk",
            task_type="walk",
            duration_minutes=20,
            priority=2,
            pet_id="pet1",
        )
    )
    assert len(pet.tasks) == 2
