from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


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


@dataclass
class Task:
	"""Represents a single activity for pet care."""

	description: str
	time: str
	frequency: str
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
			if pet.name == pet_name:
				return pet.get_tasks(include_completed=include_completed)
		return []

	def organize_tasks(self, include_completed: bool = False) -> list[Task]:
		"""Return tasks ordered by completion state, frequency, then time."""
		tasks = self.retrieve_all_tasks(include_completed=include_completed)
		return sorted(
			tasks,
			key=lambda task: (
				task.is_completed,
				_frequency_rank(task.frequency),
				_minutes_from_hhmm(task.time),
			),
		)

	def mark_task_complete(self, pet_name: str, description: str, task_time: str | None = None) -> bool:
		"""Mark the first matching task complete for the selected pet."""
		for pet in self.owner.pets:
			if pet.name != pet_name:
				continue
			for task in pet.tasks:
				if task.description != description:
					continue
				if task_time is not None and task.time != task_time:
					continue
				task.mark_complete()
				return True
		return False


