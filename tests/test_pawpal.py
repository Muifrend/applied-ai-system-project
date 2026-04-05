from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status() -> None:
    """Verify that marking a task complete updates its completion status."""
    task = Task(description="Morning walk", time="07:00", frequency="daily")
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count() -> None:
    """Verify that calling `add_task` on a `Pet` appends the provided `Task` to
    the pet's task list and increases the total task count by exactly one."""
    pet = Pet(name="Mochi", animal="dog", age=4)
    initial_count = len(pet.tasks)
    task = Task(description="Feed breakfast", time="08:00", frequency="daily")

    pet.add_task(task)

    assert len(pet.tasks) == initial_count + 1
    assert task in pet.tasks


def test_sort_by_time_orders_hhmm_values() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", animal="dog", age=4)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)

    pet.add_task(Task(description="Second", time="09:30", frequency="daily"))
    pet.add_task(Task(description="First", time="07:00", frequency="daily"))

    ordered = scheduler.sort_by_time(scheduler.retrieve_all_tasks(include_completed=False))

    assert [task.description for task in ordered] == ["First", "Second"]


def test_filter_tasks_by_pet_and_completion_status() -> None:
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", animal="dog", age=4)
    cat = Pet(name="Pixel", animal="cat", age=2)
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner=owner)

    done_task = Task(description="Walk", time="07:00", frequency="daily", is_completed=True)
    todo_task = Task(description="Brush", time="08:00", frequency="daily")
    dog.add_task(done_task)
    dog.add_task(todo_task)
    cat.add_task(Task(description="Feed", time="09:00", frequency="daily"))

    filtered = scheduler.filter_tasks(pet_name="mochi", include_completed=False)

    assert len(filtered) == 1
    assert filtered[0].description == "Brush"


def test_mark_task_complete_adds_next_occurrence_for_recurring_task() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", animal="dog", age=4)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)

    original = Task(
        description="Morning walk",
        time="07:00",
        frequency="daily",
        due_date=date(2026, 4, 5),
    )
    pet.add_task(original)

    result = scheduler.mark_task_complete("Mochi", "Morning walk", "07:00")

    assert result is True
    assert original.is_completed is True
    assert len(pet.tasks) == 2
    next_task = pet.tasks[1]
    assert next_task.description == "Morning walk"
    assert next_task.is_completed is False
    assert next_task.due_date == date(2026, 4, 6)


def test_detect_conflicts_returns_warning_instead_of_error() -> None:
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", animal="dog", age=4)
    cat = Pet(name="Pixel", animal="cat", age=2)
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner=owner)

    dog.add_task(Task(description="Medication", time="08:00", frequency="daily"))
    cat.add_task(Task(description="Breakfast", time="08:00", frequency="daily"))

    warnings = scheduler.detect_conflicts(include_completed=False)

    assert len(warnings) == 1
    assert "Conflict at" in warnings[0]
    assert "Medication" in warnings[0]
    assert "Breakfast" in warnings[0]
