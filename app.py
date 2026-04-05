from datetime import date, datetime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task, _frequency_rank, _minutes_from_hhmm


def load_dummy_owners() -> list[Owner]:
    """Seed starter owners, pets, and tasks for first app launch."""
    jordan = Owner(name="Jordan")
    alex = Owner(name="Alex")

    mochi = Pet(name="Mochi", animal="dog", age=4)
    pixel = Pet(name="Pixel", animal="cat", age=2)
    kiwi = Pet(name="Kiwi", animal="bird", age=1)

    today = date.today()
    mochi.add_task(Task(description="Morning walk", time="07:00", frequency="daily", due_date=today))
    mochi.add_task(Task(description="Lunch", time="12:00", frequency="daily", due_date=today))
    pixel.add_task(Task(description="Breakfast", time="08:00", frequency="daily", due_date=today))
    kiwi.add_task(Task(description="Cage clean", time="09:00", frequency="weekly", due_date=today))

    jordan.add_pet(mochi)
    jordan.add_pet(pixel)
    alex.add_pet(kiwi)
    return [jordan, alex]


def _find_owner_by_name(owners: list[Owner], owner_name: str) -> Owner | None:
    for owner in owners:
        if owner.name == owner_name:
            return owner
    return None


def _find_pet_by_name(owner: Owner, pet_name: str) -> Pet | None:
    for pet in owner.pets:
        if pet.name == pet_name:
            return pet
    return None


def _owners_in_view(owners: list[Owner], selected_owner_name: str) -> list[Owner]:
    if selected_owner_name == "All":
        return owners
    selected_owner = _find_owner_by_name(owners, selected_owner_name)
    if selected_owner is None:
        return owners
    return [selected_owner]


def _task_conflicts_with_existing(task: Task, pet: Pet) -> bool:
    for existing in pet.get_tasks(include_completed=False):
        if existing.due_date == task.due_date and existing.time == task.time:
            return True
    return False


def _find_pet_name_for_task(owner: Owner, task: Task) -> str | None:
    for pet in owner.pets:
        if any(existing_task is task for existing_task in pet.tasks):
            return pet.name
    return None


def _task_record_sort_key(record: tuple[str, str, Task]) -> tuple[bool, date, int, int, str, str, str, str]:
    owner_name, pet_name, task = record
    return (
        task.is_completed,
        task.due_date,
        _frequency_rank(task.frequency),
        _minutes_from_hhmm(task.time),
        owner_name.lower(),
        pet_name.lower(),
        task.description.lower(),
        task.time,
    )


def _tasks_with_owner_and_pet(
    owners: list[Owner], include_completed: bool = True
) -> list[tuple[str, str, Task]]:
    records: list[tuple[str, str, Task]] = []
    for owner in owners:
        owner_scheduler = Scheduler(owner=owner)
        for task in owner_scheduler.organize_tasks(include_completed=include_completed):
            pet_name = _find_pet_name_for_task(owner, task)
            if pet_name is None:
                continue
            records.append((owner.name, pet_name, task))
    return sorted(records, key=_task_record_sort_key)


def _pet_targets(owners: list[Owner]) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for owner in owners:
        for pet in owner.pets:
            targets.append((owner.name, pet.name))
    return targets


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

if "owners" not in st.session_state:
    st.session_state.owners = load_dummy_owners()

owners: list[Owner] = st.session_state.owners
owner_names = [owner.name for owner in owners]
owner_filter_options = ["All", *owner_names]

if "selected_owner_name" not in st.session_state:
    st.session_state.selected_owner_name = "All"

# ------------------------------------------------------------------------------
# SIDEBAR: ADD ACTIONS
# ------------------------------------------------------------------------------
st.sidebar.title("🐾 PawPal+")
st.sidebar.subheader("Quick Actions")

with st.sidebar.expander("Add New Owner", expanded=True):
    with st.form("new_owner_form"):
        new_owner_name = st.text_input("Owner name")
        owner_submit = st.form_submit_button("Add Owner")
        if owner_submit:
            clean_name = new_owner_name.strip()
            if not clean_name:
                st.warning("Owner name is required.")
            elif clean_name in owner_names:
                st.warning("Owner names must be unique.")
            else:
                owners.append(Owner(name=clean_name))
                st.session_state.selected_owner_name = clean_name
                st.success(f"Added owner {clean_name}.")
                st.rerun()

# Add New Pet
with st.sidebar.expander("Add New Pet"):
    if not owners:
        st.warning("Add an owner first!")
    with st.form("new_pet_form"):
        target_owner_name = st.selectbox("Owner", [owner.name for owner in owners], key="pet_owner_selector")
        p_name = st.text_input("Name")
        p_species = st.selectbox("Species", ["dog", "cat", "bird", "other"])
        p_age = st.number_input("Age", min_value=0, max_value=30, value=1)
        p_submit = st.form_submit_button("Add Pet")

        if p_submit and p_name.strip():
            target_owner = _find_owner_by_name(owners, target_owner_name)
            if target_owner is None:
                st.error("Selected owner could not be found.")
            else:
                target_owner.add_pet(Pet(name=p_name.strip(), animal=p_species, age=int(p_age)))
                st.success(f"Added {p_name.strip()} to {target_owner.name}.")
                st.rerun()

# Add New Task
with st.sidebar.expander("Schedule Task", expanded=True):
    targets = _pet_targets(owners)
    if not targets:
        st.warning("Add a pet first!")
    else:
        with st.form("new_task_form"):
            pet_name_counts: dict[str, int] = {}
            for _, pet_name in targets:
                pet_name_counts[pet_name] = pet_name_counts.get(pet_name, 0) + 1

            target_labels = [
                pet_name if pet_name_counts[pet_name] == 1 else f"{pet_name} ({owner_name})"
                for owner_name, pet_name in targets
            ]
            target_index = st.selectbox(
                "Pet Select",
                options=list(range(len(targets))),
                format_func=lambda idx: target_labels[idx],
            )
            t_desc = st.text_input("Task (e.g., Walk)")
            t_time = st.time_input("Time", datetime.now().time())
            t_freq = st.selectbox("Frequency", ["daily", "weekly", "monthly", "as needed"])
            t_due_date = st.date_input("Due date", value=date.today())
            t_submit = st.form_submit_button("Schedule")

            if t_submit and t_desc.strip():
                target_owner_name, target_pet_name = targets[target_index]
                target_owner = _find_owner_by_name(owners, target_owner_name)
                if target_owner is None:
                    st.error("Selected owner could not be found.")
                else:
                    target_pet = _find_pet_by_name(target_owner, target_pet_name)
                    if target_pet is None:
                        st.error("Selected pet could not be found.")
                        st.stop()

                    new_task = Task(
                        description=t_desc.strip(),
                        time=t_time.strftime("%H:%M"),
                        frequency=t_freq,
                        due_date=t_due_date,
                    )

                    if _task_conflicts_with_existing(new_task, target_pet):
                        st.error("⚠️ Conflict detected! This pet already has a task at that date and time.")
                    else:
                        target_pet.add_task(new_task)
                        st.success("Task Scheduled!")
                        st.rerun()

# ------------------------------------------------------------------------------
# MAIN DASHBOARD
# ------------------------------------------------------------------------------
st.title("Today's Schedule")
selected_owner_name = st.selectbox(
    "Owner filter",
    options=owner_filter_options,
    index=(
        owner_filter_options.index(st.session_state.selected_owner_name)
        if st.session_state.selected_owner_name in owner_filter_options
        else 0
    ),
)
st.session_state.selected_owner_name = selected_owner_name
view_owners = _owners_in_view(owners, selected_owner_name)
st.caption(
    "Showing tasks for all owners"
    if selected_owner_name == "All"
    else f"Showing tasks for: {selected_owner_name}"
)

show_completed = st.checkbox("Show completed tasks", value=False)

pending_count = sum(len(owner.get_all_tasks(include_completed=False)) for owner in view_owners)
pets_count = sum(len(owner.pets) for owner in view_owners)

col1, col2, col3 = st.columns(3)
col1.metric("Owners Managed", len(owners))
col2.metric("Pets Managed", pets_count)
col3.metric("Pending Tasks", pending_count)

st.divider()

tasks = _tasks_with_owner_and_pet(view_owners, include_completed=show_completed)

if not tasks:
    st.info("No upcoming tasks! Relax with your furry friends.")
else:
    for row_index, (owner_name, pet_name, task) in enumerate(tasks):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])

            with c1:
                try:
                    label_time = datetime.strptime(task.time, "%H:%M").strftime("%I:%M %p")
                except ValueError:
                    label_time = task.time
                st.write(f"**{label_time}**")

            with c2:
                if task.is_completed:
                    st.markdown(f"~~{owner_name} > {pet_name}: {task.description}~~")
                else:
                    st.markdown(f"**{owner_name} > {pet_name}**: {task.description}")
                st.caption(f"Due {task.due_date.isoformat()} | {task.frequency}")

            with c3:
                if not task.is_completed:
                    done_key = f"done_{row_index}_{id(task)}"
                    if st.button("Done", key=done_key):
                        owner_for_task = _find_owner_by_name(owners, owner_name)
                        if owner_for_task is None:
                            st.error("Owner for this task was not found.")
                            st.stop()

                        owner_scheduler = Scheduler(owner=owner_for_task)
                        was_marked = owner_scheduler.mark_task_complete(
                            pet_name=pet_name,
                            description=task.description,
                            task_time=task.time,
                            task_due_date=task.due_date,
                        )
                        if not was_marked:
                            st.error("That task could not be completed. Please try again.")
                        else:
                            st.rerun()
                else:
                    st.write("✅")

conflict_warnings: list[str] = []
for owner in view_owners:
    owner_scheduler = Scheduler(owner=owner)
    for warning in owner_scheduler.detect_conflicts(include_completed=False):
        conflict_warnings.append(f"{owner.name}: {warning}")

if conflict_warnings:
    st.markdown("### Conflict Warnings")
    for warning in conflict_warnings:
        st.warning(warning)

# ------------------------------------------------------------------------------
# DEBUG / INSPECTOR
# ------------------------------------------------------------------------------
with st.expander("Debug: Raw System Data"):
    st.write(owners)
