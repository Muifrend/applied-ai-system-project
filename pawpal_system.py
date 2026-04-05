from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


def _minutes_from_hhmm(time_str: str) -> int:
	"""Convert HH:MM string to minutes from midnight for sorting."""
	try:
		parsed = datetime.strptime(time_str, "%H:%M")
		return parsed.hour * 60 + parsed.minute
	except ValueError:
		# Unknown format sorts to the end instead of breaking scheduling.
		return 24 * 60 + 1


def _frequency_rank(frequency: str) -> int:
	"""Higher rank means task should usually be scheduled earlier."""
	order = {
		"daily": 0,
		"weekly": 1,
		"monthly": 2,
		"as needed": 3,
	}
	return order.get(frequency.strip().lower(), 4)


def _next_due_date(current_due_date: date, frequency: str) -> date | None:
	"""Return the next due date for recurring frequencies."""
	normalized = frequency.strip().lower()
	if normalized == "daily":
		return current_due_date + timedelta(days=1)
	if normalized == "weekly":
		return current_due_date + timedelta(days=7)
	if normalized == "monthly":
		# Lightweight monthly handling: 30-day approximation for this project scope.
		return current_due_date + timedelta(days=30)
	return None


@dataclass
class Task:
	"""Represents a single activity for pet care."""

	description: str
	time: str
	frequency: str
	due_date: date = field(default_factory=date.today)
	is_completed: bool = False

	def mark_complete(self) -> None:
		self.is_completed = True

	def mark_incomplete(self) -> None:
		self.is_completed = False

	def update(self, description: str | None = None, time: str | None = None, frequency: str | None = None) -> None:
		if description is not None:
			self.description = description
		if time is not None:
			self.time = time
		if frequency is not None:
			self.frequency = frequency

	def build_next_occurrence(self) -> Task | None:
		"""Create the next recurring task instance if frequency supports recurrence."""
		next_due_date = _next_due_date(self.due_date, self.frequency)
		if next_due_date is None:
			return None
		return Task(
			description=self.description,
			time=self.time,
			frequency=self.frequency,
			due_date=next_due_date,
		)


@dataclass
class Pet:
	"""Stores basic pet details and all tasks for that pet."""

	name: str
	animal: str
	age: int
	is_sick: bool = False
	tasks: list[Task] = field(default_factory=list)

	def set_sick(self, status: bool) -> None:
		self.is_sick = status

	def add_task(self, task: Task) -> None:
		self.tasks.append(task)

	def remove_task(self, task: Task) -> bool:
		if task in self.tasks:
			self.tasks.remove(task)
			return True
		return False

	def get_tasks(self, include_completed: bool = True) -> list[Task]:
		if include_completed:
			return list(self.tasks)
		return [task for task in self.tasks if not task.is_completed]


@dataclass
class Owner:
	"""Manages multiple pets and provides cross-pet task access."""

	name: str
	pets: list[Pet] = field(default_factory=list)

	def add_pet(self, pet: Pet) -> None:
		self.pets.append(pet)

	def remove_pet(self, pet: Pet) -> bool:
		if pet in self.pets:
			self.pets.remove(pet)
			return True
		return False

	def get_all_tasks(self, include_completed: bool = True) -> list[Task]:
		all_tasks: list[Task] = []
		for pet in self.pets:
			all_tasks.extend(pet.get_tasks(include_completed=include_completed))
		return all_tasks

	def get_tasks_by_pet(self) -> dict[str, list[Task]]:
		return {pet.name: list(pet.tasks) for pet in self.pets}


@dataclass
class Scheduler:
	"""The brain that retrieves, organizes, and manages tasks across pets."""

	owner: Owner

	def retrieve_all_tasks(self, include_completed: bool = True) -> list[Task]:
		return self.owner.get_all_tasks(include_completed=include_completed)

	def retrieve_tasks_for_pet(self, pet_name: str, include_completed: bool = True) -> list[Task]:
		for pet in self.owner.pets:
			if pet.name.lower() == pet_name.lower():
				return pet.get_tasks(include_completed=include_completed)
		return []

	def filter_tasks(self, pet_name: str | None = None, include_completed: bool = True) -> list[Task]:
		"""Filter tasks by optional pet name and completion status."""
		if pet_name is None:
			return self.retrieve_all_tasks(include_completed=include_completed)
		return self.retrieve_tasks_for_pet(pet_name=pet_name, include_completed=include_completed)

	def sort_by_time(self, tasks: list[Task]) -> list[Task]:
		"""Return tasks ordered by due date then HH:MM time."""
		return sorted(tasks, key=lambda task: (task.due_date, _minutes_from_hhmm(task.time)))

	def organize_tasks(self, include_completed: bool = False) -> list[Task]:
		"""Return tasks ordered by completion state, frequency, then time."""
		tasks = self.retrieve_all_tasks(include_completed=include_completed)
		return sorted(
			tasks,
			key=lambda task: (
				task.is_completed,
				task.due_date,
				_frequency_rank(task.frequency),
				_minutes_from_hhmm(task.time),
			),
		)

	def mark_task_complete(self, pet_name: str, description: str, task_time: str | None = None) -> bool:
		"""Mark matching task complete and auto-create next recurring occurrence."""
		for pet in self.owner.pets:
			if pet.name.lower() != pet_name.lower():
				continue
			for task in pet.tasks:
				if task.description != description:
					continue
				if task_time is not None and task.time != task_time:
					continue
				task.mark_complete()
				next_task = task.build_next_occurrence()
				if next_task is not None:
					pet.add_task(next_task)
				return True
		return False

	def detect_conflicts(self, pet_name: str | None = None, include_completed: bool = False) -> list[str]:
		"""Detect exact slot conflicts and return warnings without raising errors."""
		tasks = self.filter_tasks(pet_name=pet_name, include_completed=include_completed)
		slot_map: dict[tuple[date, str], list[tuple[str, Task]]] = {}
		for pet in self.owner.pets:
			if pet_name is not None and pet.name.lower() != pet_name.lower():
				continue
			for task in pet.get_tasks(include_completed=include_completed):
				slot = (task.due_date, task.time)
				slot_map.setdefault(slot, []).append((pet.name, task))

		warnings: list[str] = []
		for (due_date, task_time), task_group in slot_map.items():
			if len(task_group) < 2:
				continue
			participants = ", ".join(
				f"{pet_name_item}: {task_item.description}"
				for pet_name_item, task_item in task_group
			)
			warnings.append(
				f"Conflict at {due_date.isoformat()} {task_time} -> {participants}"
			)
		return warnings


