from pawpal_system import Owner, Pet, Scheduler, Task


def build_sample_data() -> Owner:
	"""Build sample owner/pet/task data including out-of-order tasks and a conflict."""
	owner = Owner(name="Jordan")

	dog = Pet(name="Mochi", animal="dog", age=4)
	cat = Pet(name="Pixel", animal="cat", age=2)

	owner.add_pet(dog)
	owner.add_pet(cat)

	dog.add_task(Task(description="Morning walk", time="07:00", frequency="daily"))
	dog.add_task(Task(description="Evening walk", time="18:30", frequency="daily"))
	cat.add_task(Task(description="Feed dinner", time="19:00", frequency="daily"))
	cat.add_task(Task(description="Play session", time="06:30", frequency="weekly"))
	dog.add_task(Task(description="Vet reminder", time="06:45", frequency="as needed"))

	# Intentional same-time conflict for demonstration.
	dog.add_task(Task(description="Medication", time="08:00", frequency="daily"))
	cat.add_task(Task(description="Breakfast", time="08:00", frequency="daily"))

	return owner


def print_task_rows(header: str, tasks: list[Task]) -> None:
	"""Print tasks in a consistent row format for terminal algorithm demos."""
	print(f"\n=== {header} ===")
	if not tasks:
		print("(none)")
		return
	for task in tasks:
		print(
			f"{task.due_date.isoformat()} {task.time} - "
			f"{task.description} [{task.frequency}] completed={task.is_completed}"
		)


if __name__ == "__main__":
	owner = build_sample_data()
	scheduler = Scheduler(owner)

	print(f"Owner: {owner.name}")

	print_task_rows("All Tasks (Raw Order)", scheduler.retrieve_all_tasks(include_completed=False))

	print_task_rows(
		"Sorted By Time",
		scheduler.sort_by_time(scheduler.retrieve_all_tasks(include_completed=False)),
	)

	print_task_rows(
		"Filtered: Mochi Incomplete",
		scheduler.filter_tasks(pet_name="Mochi", include_completed=False),
	)

	print("\nMarking 'Morning walk' complete for Mochi (recurring daily)...")
	scheduler.mark_task_complete("Mochi", "Morning walk", "07:00")

	print_task_rows(
		"Mochi Tasks After Completion (Recurring Auto-Added)",
		scheduler.filter_tasks(pet_name="Mochi", include_completed=True),
	)

	conflicts = scheduler.detect_conflicts(include_completed=False)
	print("\n=== Conflict Warnings ===")
	if conflicts:
		for warning in conflicts:
			print(f"WARNING: {warning}")
	else:
		print("No conflicts detected.")
