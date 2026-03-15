# PawPal+ Class Diagram

Mermaid.js class diagram for the pet care app (Owner, Pet, Task, Scheduler).

```mermaid
classDiagram
    class Owner {
        +name: str
        +available_start: time
        +available_end: time
        +preferences: str
        +pets: list
        +tasks: list
        +get_available_minutes() int
        +is_available(at_time) bool
        +get_constraints() dict
    }

    class Pet {
        +name: str
        +species: str
        +__str__() str
        +get_care_notes() str
    }

    class Task {
        +id: str
        +name: str
        +task_type: str
        +duration_minutes: int
        +priority: int
        +preferred_time: time
        +pet_id: str
        +get_duration_minutes() int
        +to_dict() dict
    }

    class Scheduler {
        +generate_plan(tasks, owner, date, pet) list
        -_sort_by_priority(tasks) list
        -_fit_into_windows(tasks, start, end) list
        +explain_plan(scheduled_items) str
    }

    Owner "1" --> "*" Pet : has
    Owner "1" --> "*" Task : has
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
  (Use a `.mmd` file containing only the mermaid code if the CLI doesn’t accept `.md`.)
