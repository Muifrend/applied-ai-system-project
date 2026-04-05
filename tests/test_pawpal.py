from pawpal_system import Pet, Task


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
