import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

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

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes today", min_value=1, max_value=1440, value=120)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Set owner & pet"):
    st.session_state.owner = Owner(owner_name, int(available_minutes))
    st.session_state.pet = Pet(pet_name, species)

if "owner" in st.session_state:
    st.success(f"Owner: {st.session_state.owner.name} | Pet: {st.session_state.pet.name} ({st.session_state.pet.species})")

st.markdown("### Tasks")
st.caption("Add tasks below — they will be attached to your pet and fed into the scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    if "pet" not in st.session_state:
        st.warning("Set an owner & pet first before adding tasks.")
    else:
        task = Task(title=task_title, duration_minutes=int(duration), priority=priority)
        st.session_state.pet.add_task(task)

if "pet" in st.session_state and st.session_state.pet.tasks:
    st.write("Current tasks:")
    st.table([
        {"title": t.title, "duration_minutes": t.duration_minutes, "priority": t.priority, "status": t.status}
        for t in st.session_state.pet.tasks
    ])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if "owner" not in st.session_state or "pet" not in st.session_state:
        st.warning("Set an owner & pet first.")
    elif not st.session_state.pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner, pet=st.session_state.pet)
        plan = scheduler.generate_plan()
        st.success(f"Schedule generated — {plan.total_minutes_used} min used.")
        st.text(plan.explanation)
        if plan.selected_tasks:
            st.table([
                {"title": t.title, "duration_minutes": t.duration_minutes, "priority": t.priority}
                for t in plan.selected_tasks
            ])
