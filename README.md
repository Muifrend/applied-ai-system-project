# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

## Smarter Scheduling

Recent scheduling upgrades include:

- Sorting tasks by due date and time for a cleaner daily plan
- Filtering tasks by pet and completion status
- Auto-creating the next occurrence for recurring tasks (daily/weekly/monthly)
- Lightweight conflict warnings for tasks that share the same scheduled slot

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

Current automated tests cover the core scheduler behaviors, including:

- Marking tasks complete and updating completion status
- Adding tasks to pets and validating task-list growth
- Chronological sorting by due date and time
- Filtering tasks by pet name and completion state
- Daily recurrence creation when a recurring task is completed
- Duplicate time-slot conflict detection with warning messages

Confidence Level: 4/5 stars

Rationale: The current suite passes and validates the most important scheduling paths, especially sorting, recurrence, and conflict warnings. Reliability is high for implemented core logic, with room to improve confidence further by adding more edge-case and UI integration tests.
