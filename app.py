import streamlit as st
from datetime import date, time

from pawpal_system import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    Owner,
    Pet,
    Scheduler,
    Task,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# --- Session state: Owner (and its pets/tasks) live here so they persist across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        available_start=time(8, 0),
        available_end=time(18, 0),
        pets=[],
    )
if "task_id_counter" not in st.session_state:
    st.session_state.task_id_counter = 0
if "pet_id_counter" not in st.session_state:
    st.session_state.pet_id_counter = 0

owner = st.session_state.owner

st.subheader("Owner & availability")
col_owner, col_start, col_end = st.columns(3)
with col_owner:
    owner_name = st.text_input("Owner name", value=owner.name, key="owner_name")
with col_start:
    start_h = st.number_input("Available from (hour)", 0, 23, 8, key="start_h")
with col_end:
    end_h = st.number_input("Available until (hour)", 0, 23, 18, key="end_h")

owner.name = owner_name
owner.available_start = time(int(start_h), 0)
owner.available_end = time(int(end_h), 0)

st.subheader("Add a pet")
pet_name = st.text_input("Pet name", value="Mochi", key="pet_name")
species = st.selectbox("Species", ["dog", "cat", "other"], key="species")

if st.button("Add pet"):
    st.session_state.pet_id_counter += 1
    pid = f"pet_{st.session_state.pet_id_counter}"
    new_pet = Pet(id=pid, name=pet_name, species=species)
    owner.pets.append(new_pet)
    st.success(f"Added {new_pet}. You can now add tasks for this pet.")
    st.rerun()

st.markdown("### Add a task")
st.caption("Select a pet, then add tasks. These feed into the scheduler.")

if not owner.pets:
    st.info("Add a pet above first, then add tasks for that pet.")
else:
    pet_options = {str(p): p for p in owner.pets}
    selected_label = st.selectbox(
        "Add task to pet",
        options=list(pet_options.keys()),
        key="task_pet_select",
    )
    selected_pet = pet_options[selected_label]

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk", key="task_title")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20, key="duration")
    with col3:
        priority_label = st.selectbox("Priority", ["high", "medium", "low"], index=0, key="priority_label")

    priority_map = {"high": PRIORITY_HIGH, "medium": PRIORITY_MEDIUM, "low": PRIORITY_LOW}

    if st.button("Add task"):
        st.session_state.task_id_counter += 1
        tid = f"task_{st.session_state.task_id_counter}"
        task = Task(
            id=tid,
            name=task_title,
            description=task_title,
            task_type="general",
            duration_minutes=int(duration),
            priority=priority_map[priority_label],
            pet_id=selected_pet.id,
        )
        selected_pet.tasks.append(task)
        st.success(f"Added task «{task_title}» for {selected_pet.name}.")
        st.rerun()

st.markdown("### Current tasks (by pet)")
if owner.pets:
    for pet in owner.pets:
        with st.expander(f"🐾 {pet.name} ({pet.species}) — {len(pet.tasks)} task(s)"):
            if pet.tasks:
                for t in pet.tasks:
                    st.write(f"- **{t.name}** — {t.duration_minutes} min, priority {t.priority}")
            else:
                st.caption("No tasks yet.")
else:
    st.caption("No pets yet. Add a pet above.")

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet and one task, then try again.")
    else:
        scheduler = Scheduler()
        today = date.today()
        schedule = scheduler.generate_plan(None, owner, today)
        explanation = scheduler.explain_plan(schedule)
        st.success(f"**Today's schedule** ({today.strftime('%A, %B %d')})")
        if schedule:
            for item in schedule:
                t = item["task"]
                start = item["start_time"]
                end = item["end_time"]
                st.write(f"**{start.strftime('%H:%M')}–{end.strftime('%H:%M')}** — {t.name} ({t.duration_minutes} min)")
            st.caption(explanation)
        else:
            st.info("No tasks could be fitted into your available time.")
