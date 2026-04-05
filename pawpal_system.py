from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pet:
	name: str
	animal: str
	age: int
	is_sick: bool = False

	def set_sick(self, status: bool) -> None:
		self.is_sick = status


@dataclass
class Task:
	name: str
	description: str
	duration_minutes: int
	priority: str
	task_type: str
	date: str
	start_time: str


@dataclass
class Owner:
	name: str
	available_minutes_per_day: int
	pets: list[Pet] = field(default_factory=list)

	def add_pet(self, pet: Pet) -> None:
		self.pets.append(pet)


@dataclass
class Schedule:
	date: str
	owner: Owner
	tasks: list[Task] = field(default_factory=list)

	def generate(self, tasks: list[Task]) -> None:
		"""Placeholder schedule generation method.

		Later, this should apply constraints (time, priority, preferences)
		and populate self.tasks with the chosen order.
		"""
		self.tasks = list(tasks)

	def add_task(self, task: Task) -> None:
		self.tasks.append(task)

	def total_minutes(self) -> int:
		return sum(task.duration_minutes for task in self.tasks)
