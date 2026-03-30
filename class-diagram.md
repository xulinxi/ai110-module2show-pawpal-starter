# PawPal+ Class Diagram

Mermaid.js class diagram for the pet care app (Owner, Pet, Task, Scheduler).

```mermaid
classDiagram
    class Owner {
        +name: str
        +available_start: time
        +available_end: time
        +preferences: str
        +pets: list~Pet~
        +get_all_tasks() list~Task~
        +get_available_minutes() int
        +is_available(at_time) bool
        +get_constraints() dict
    }

    class Pet {
        +id: str
        +name: str
        +species: str
        +care_notes: str
        +tasks: list~Task~
        +__str__() str
        +get_care_notes() str
    }

    class Task {
        +id: str
        +name: str
        +description: str
        +task_type: str
        +duration_minutes: int
        +priority: int
        +preferred_time: time
        +pet_id: str
        +frequency: str
        +completion_status: bool
        +get_duration_minutes() int
        +mark_complete() void
        +to_dict() dict
    }

    class Scheduler {
        +generate_plan(tasks, owner, date, pet) list
        +sort_by_time(tasks) list~Task~
        +filter_by_status(tasks, completed) list~Task~
        +filter_by_pet(tasks, pet_name, pets) list~Task~
        +mark_task_complete(task, all_tasks) Task
        +detect_conflicts(scheduled_items) list~str~
        +explain_plan(scheduled_items) str
        -_sort_by_priority(tasks) list~Task~
        -_fit_into_windows(tasks, start, end) list
    }

    Owner "1" --> "*" Pet : has
    Pet "1" --> "*" Task : has
    Task "*" --> "0..1" Pet : pet_id references
    Scheduler ..> Task : uses
    Scheduler ..> Owner : uses
    Scheduler ..> Pet : uses
```

## How to view

- **GitHub / GitLab**: Paste the mermaid block into a `.md` file; it will render in the repo.
- **VS Code / Cursor**: Use a Mermaid preview extension (e.g. "Markdown Preview Mermaid Support").
- **Online**: Copy the diagram code into [Mermaid Live Editor](https://mermaid.live).
- **CLI (PNG/SVG)**: Install `@mermaid-js/mermaid-cli` then run:
  ```bash
  mmdc -i class-diagram.md -o diagram.svg
  ```
  (Use a `.mmd` file containing only the mermaid code if the CLI doesn't accept `.md`.)
