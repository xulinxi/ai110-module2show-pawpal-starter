import streamlit as st
from datetime import date, time
from pathlib import Path

from pawpal_system import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    Owner,
    Pet,
    Scheduler,
    Task,
)

DATA_FILE = Path("data.json")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    "A smart pet care planning assistant that schedules, sorts, filters, "
    "detects conflicts, and handles recurring tasks automatically."
)

# --- Session state (with JSON persistence) ----------------------------------
if "owner" not in st.session_state:
    if DATA_FILE.exists():
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
        st.toast("Loaded saved data from data.json")
    else:
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


def _save() -> None:
    """Persist current owner state to data.json."""
    st.session_state.owner.save_to_json(DATA_FILE)


owner = st.session_state.owner
scheduler = Scheduler()

# --- Owner & availability ---------------------------------------------------
st.subheader("Owner & Availability")
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

# --- Add a pet --------------------------------------------------------------
st.subheader("Add a Pet")
pet_name = st.text_input("Pet name", value="Mochi", key="pet_name")
species = st.selectbox("Species", ["dog", "cat", "other"], key="species")

if st.button("Add pet"):
    st.session_state.pet_id_counter += 1
    pid = f"pet_{st.session_state.pet_id_counter}"
    new_pet = Pet(id=pid, name=pet_name, species=species)
    owner.pets.append(new_pet)
    _save()
    st.success(f"Added {new_pet}. You can now add tasks for this pet.")
    st.rerun()

# --- Add a task -------------------------------------------------------------
st.subheader("Add a Task")
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
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="duration")
    with col3:
        priority_label = st.selectbox("Priority", ["high", "medium", "low"], index=0, key="priority_label")

    col4, col5, col6 = st.columns(3)
    with col4:
        pref_hour = st.number_input("Preferred hour", 0, 23, 9, key="pref_hour")
        pref_min = st.number_input("Preferred minute", 0, 59, 0, key="pref_min")
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"], key="frequency")
    with col6:
        task_type = st.selectbox(
            "Task type",
            ["walk", "feeding", "meds", "enrichment", "grooming", "general"],
            key="task_type",
        )

    priority_map = {"high": PRIORITY_HIGH, "medium": PRIORITY_MEDIUM, "low": PRIORITY_LOW}

    if st.button("Add task"):
        st.session_state.task_id_counter += 1
        tid = f"task_{st.session_state.task_id_counter}"
        task = Task(
            id=tid,
            name=task_title,
            description=task_title,
            task_type=task_type,
            duration_minutes=int(duration),
            priority=priority_map[priority_label],
            preferred_time=time(int(pref_hour), int(pref_min)),
            pet_id=selected_pet.id,
            frequency=frequency,
        )
        selected_pet.tasks.append(task)
        _save()
        st.success(f"Added task \"{task_title}\" for {selected_pet.name}.")
        st.rerun()

# --- Current tasks (sorted by time, with filters & emoji formatting) --------
st.divider()
st.subheader("Current Tasks")

all_tasks = owner.get_all_tasks()

if all_tasks:
    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        pet_filter = st.selectbox(
            "Filter by pet",
            ["All pets"] + [p.name for p in owner.pets],
            key="pet_filter",
        )
    with col_f2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Incomplete", "Completed"],
            key="status_filter",
        )

    display_tasks = all_tasks
    if pet_filter != "All pets":
        display_tasks = scheduler.filter_by_pet(display_tasks, pet_filter, owner.pets)
    if status_filter == "Incomplete":
        display_tasks = scheduler.filter_by_status(display_tasks, completed=False)
    elif status_filter == "Completed":
        display_tasks = scheduler.filter_by_status(display_tasks, completed=True)

    # Sort by preferred time
    display_tasks = scheduler.sort_by_time(display_tasks)

    if display_tasks:
        table_data = []
        for t in display_tasks:
            ptime = t.preferred_time.strftime("%H:%M") if t.preferred_time else "—"
            pet_name_display = next((p.name for p in owner.pets if p.id == t.pet_id), "—")
            table_data.append({
                "Time": ptime,
                "Task": t.name,
                "Type": scheduler.format_task_type(t.task_type),
                "Pet": pet_name_display,
                "Duration": f"{t.duration_minutes} min",
                "Priority": scheduler.format_priority(t.priority),
                "Frequency": t.frequency.capitalize(),
                "Status": scheduler.format_status(t.completion_status),
            })
        st.table(table_data)
    else:
        st.caption("No tasks match your filters.")

    # Mark complete
    incomplete = scheduler.filter_by_status(all_tasks, completed=False)
    if incomplete:
        task_to_complete = st.selectbox(
            "Mark a task complete",
            options=[t.name for t in incomplete],
            key="complete_select",
        )
        if st.button("Mark complete"):
            task_obj = next(t for t in incomplete if t.name == task_to_complete)
            new_task = scheduler.mark_task_complete(task_obj, all_tasks)
            if new_task:
                for pet in owner.pets:
                    if pet.id == new_task.pet_id:
                        pet.tasks.append(new_task)
                        break
                st.success(f"Completed \"{task_obj.name}\" — next {task_obj.frequency} occurrence created automatically.")
            else:
                st.success(f"Completed \"{task_obj.name}\".")
            _save()
            st.rerun()
else:
    st.caption("No tasks yet. Add a pet and some tasks above.")

# --- Generate schedule ------------------------------------------------------
st.divider()
st.subheader("📅 Daily Schedule")

if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet and one task, then try again.")
    else:
        today = date.today()
        schedule = scheduler.generate_plan(None, owner, today)
        explanation = scheduler.explain_plan(schedule)

        st.success(f"**Schedule for {today.strftime('%A, %B %d, %Y')}**")

        if schedule:
            schedule_data = []
            for item in schedule:
                t = item["task"]
                start = item["start_time"]
                end = item["end_time"]
                pet_name_display = next((p.name for p in owner.pets if p.id == t.pet_id), "—")
                schedule_data.append({
                    "Start": start.strftime("%H:%M"),
                    "End": end.strftime("%H:%M"),
                    "Task": t.name,
                    "Type": scheduler.format_task_type(t.task_type),
                    "Pet": pet_name_display,
                    "Priority": scheduler.format_priority(t.priority),
                    "Duration": f"{t.duration_minutes} min",
                })
            st.table(schedule_data)
            st.caption(explanation)

            # Conflict detection
            warnings = scheduler.detect_conflicts(schedule)
            if warnings:
                for w in warnings:
                    st.warning(f"⚠️ {w}")
            else:
                st.success("✅ No scheduling conflicts detected.")

            # Next available slot suggestion (Challenge 1)
            st.divider()
            st.markdown("#### 🔍 Find Next Available Slot")
            slot_duration = st.number_input(
                "Task duration to fit (minutes)", min_value=1, max_value=240, value=15, key="slot_dur"
            )
            next_slot = scheduler.find_next_available_slot(schedule, int(slot_duration), owner)
            if next_slot:
                st.info(f"Next available {slot_duration}-minute slot starts at **{next_slot.strftime('%H:%M')}**.")
            else:
                st.warning(f"No {slot_duration}-minute slot available in today's schedule.")
        else:
            st.info("No tasks could be fitted into your available time window.")

# --- Persistence controls ---------------------------------------------------
st.divider()
col_save, col_clear = st.columns(2)
with col_save:
    if st.button("💾 Save data"):
        _save()
        st.success(f"Saved to {DATA_FILE}.")
with col_clear:
    if st.button("🗑️ Clear saved data"):
        if DATA_FILE.exists():
            DATA_FILE.unlink()
        st.session_state.owner = Owner(
            name="Jordan",
            available_start=time(8, 0),
            available_end=time(18, 0),
            pets=[],
        )
        st.success("Cleared all data.")
        st.rerun()
