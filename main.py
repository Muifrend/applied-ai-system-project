from pawpal_system import Owner, Pet, Task


def build_sample_data() -> Owner:
	owner = Owner(name="Jordan")

	dog = Pet(name="Mochi", animal="dog", age=4)
	cat = Pet(name="Pixel", animal="cat", age=2)

	owner.add_pet(dog)
	owner.add_pet(cat)

	dog.add_task(Task(description="Morning walk", time="07:00", frequency="daily"))
	dog.add_task(Task(description="Evening walk", time="18:30", frequency="daily"))
	cat.add_task(Task(description="Feed dinner", time="19:00", frequency="daily"))

	return owner


if __name__ == "__main__":
	owner = build_sample_data()
	print(f"Owner: {owner.name}")
	for pet in owner.pets:
		print(f"- {pet.name} ({pet.animal})")
		for task in pet.tasks:
			print(f"  * {task.time} - {task.description} [{task.frequency}]")
