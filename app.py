import streamlit as st
from datetime import datetime, time as dt_time

from pawpal_system import Owner, Pet, Task, Priority, Frequency, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ helps a pet owner plan care tasks for their pets — feedings, walks,
medications, and appointments — and builds a prioritized daily schedule.
"""
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care
tasks for their pet(s) based on constraints like available time and task
priority, and flags any scheduling conflicts it finds.
"""
    )

st.divider()

# ---------------------------------------------------------------------------
# Application "memory"
#
# Streamlit reruns this whole script top-to-bottom on every interaction, so
# the Owner object (and everything inside it) is stored in st.session_state
# instead of a plain local variable — otherwise it would be recreated empty
# every time a button is clicked.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

if "pets" not in st.session_state:
    st.session_state.pets = {}  # name -> Pet

# ---- Owner setup -----------------------------------------------------

st.subheader("1. Owner")
owner_name = st.text_input("Owner name", value="Jordan")
if st.session_state.owner is None or st.session_state.owner.name != owner_name:
    st.session_state.owner = Owner(name=owner_name)
    # re-attach any pets already created this session
    for pet in st.session_state.pets.values():
        st.session_state.owner.add_pet(pet)

# ---- Add a pet -----------------------------------------------------

st.subheader("2. Pets")
col_a, col_b = st.columns(2)
with col_a:
    new_pet_name = st.text_input("Pet name", value="Biscuit")
with col_b:
    new_pet_species = st.selectbox("Species", ["Dog", "Cat", "Other"])

if st.button("Add pet"):
    if new_pet_name and new_pet_name not in st.session_state.pets:
        pet = Pet(name=new_pet_name, species=new_pet_species)
        st.session_state.pets[new_pet_name] = pet
        st.session_state.owner.add_pet(pet)
        st.success(f"Added {new_pet_name} the {new_pet_species}.")
    elif new_pet_name in st.session_state.pets:
        st.warning(f"{new_pet_name} has already been added.")

if st.session_state.pets:
    st.write("Current pets:", ", ".join(st.session_state.pets.keys()))
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---- Add a task -----------------------------------------------------

st.subheader("3. Tasks")

if st.session_state.pets:
    task_pet_name = st.selectbox("Which pet?", list(st.session_state.pets.keys()))

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        task_time = st.time_input("Time", value=dt_time(8, 0))
    with col3:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)

    col4, col5 = st.columns(2)
    with col4:
        priority_label = st.selectbox("Priority", ["Low", "Medium", "High"], index=2)
    with col5:
        frequency_label = st.selectbox("Frequency", ["Once", "Daily", "Weekly"], index=0)

    if st.button("Add task"):
        task = Task(
            description=task_title,
            scheduled_time=task_time,
            duration_minutes=int(duration),
            priority=Priority[priority_label.upper()],
            frequency=Frequency[frequency_label.upper()],
        )
        st.session_state.pets[task_pet_name].add_task(task)
        st.success(f"Added '{task_title}' for {task_pet_name}.")
else:
    st.info("Add a pet first before adding tasks.")

# Show current tasks across all pets
all_tasks = st.session_state.owner.all_tasks() if st.session_state.owner else []
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Pet": next(
                    p.name for p in st.session_state.pets.values() if t in p.tasks
                ),
                "Task": t.description,
                "Time": t.scheduled_time.strftime("%I:%M %p"),
                "Duration (min)": t.duration_minutes,
                "Priority": str(t.priority),
                "Frequency": t.frequency.value,
            }
            for t in all_tasks
        ]
    )

st.divider()

# ---- Build schedule -----------------------------------------------------

st.subheader("4. Build Schedule")
minutes_available = st.number_input(
    "Time budget for today (minutes, optional — leave at 0 for no limit)",
    min_value=0,
    max_value=1000,
    value=0,
)

if st.button("Generate schedule"):
    if not st.session_state.owner or not st.session_state.owner.pets:
        st.warning("Add at least one pet and a task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        budget = minutes_available if minutes_available > 0 else None
        result = scheduler.build_daily_plan(minutes_available=budget)

        st.markdown("### 📋 Today's Plan")
        if not result["plan"]:
            st.info("No tasks to schedule yet.")
        for task in result["plan"]:
            pet_name = next(
                p.name for p in st.session_state.pets.values() if task in p.tasks
            )
            st.write(f"**{task.scheduled_time.strftime('%I:%M %p')}** — {task.description} "
                      f"({task.duration_minutes} min, {task.priority}) — *{pet_name}*")

        if result["skipped"]:
            st.markdown("### ⏭️ Skipped (ran out of time budget)")
            for task in result["skipped"]:
                st.write(f"- {task.description} ({task.duration_minutes} min)")

        if result["conflicts"]:
            st.markdown("### ⚠️ Scheduling Conflicts")
            for a, b in result["conflicts"]:
                st.warning(f"'{a.description}' overlaps with '{b.description}'")
        else:
            st.success("No scheduling conflicts detected.")
