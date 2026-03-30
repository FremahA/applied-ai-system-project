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

# ---------------------------------------------------------------------------
# Step 1 — Owner
# ---------------------------------------------------------------------------
st.subheader("1. Owner")

owner_name = st.text_input("Owner name", value="Jordan")
col_time, col_buf = st.columns(2)
with col_time:
    available_minutes = st.number_input(
        "Available minutes today", min_value=1, max_value=1440, value=120
    )
with col_buf:
    buffer_minutes = st.number_input(
        "Buffer between tasks (min)", min_value=0, max_value=60, value=5,
        help="Rest/travel time inserted between consecutive tasks",
    )

if st.button("Create owner"):
    st.session_state.owner = Owner(
        owner_name, int(available_minutes), buffer_minutes=int(buffer_minutes)
    )

if "owner" in st.session_state:
    o = st.session_state.owner
    st.success(f"{o.name} — {o.available_minutes} min available, {o.buffer_minutes} min buffer")

st.divider()

# ---------------------------------------------------------------------------
# Step 2 — Pets
# ---------------------------------------------------------------------------
st.subheader("2. Pets")

if "owner" not in st.session_state:
    st.info("Create an owner first.")
else:
    col_pname, col_species = st.columns(2)
    with col_pname:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col_species:
        species = st.selectbox("Species", ["dog", "cat", "other"])

    if st.button("Add pet"):
        new_pet = Pet(pet_name, species)
        st.session_state.owner.pets.append(new_pet)

    if st.session_state.owner.pets:
        st.write("Your pets:")
        st.table([
            {"name": p.name, "species": p.species, "tasks": len(p.tasks)}
            for p in st.session_state.owner.pets
        ])
    else:
        st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Step 3 — Tasks
# ---------------------------------------------------------------------------
st.subheader("3. Tasks")

if "owner" not in st.session_state or not st.session_state.owner.pets:
    st.info("Add at least one pet first.")
else:
    pets = st.session_state.owner.pets
    pet_names = [p.name for p in pets]

    selected_pet_name = st.selectbox("Add task to pet", pet_names, key="task_target_pet")
    target_pet = next(p for p in pets if p.name == selected_pet_name)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        required = st.checkbox(
            "Required", value=False,
            help="Always include regardless of time pressure",
        )

    if st.button("Add task"):
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            required=required,
        )
        target_pet.add_task(task)

    for pet in pets:
        if pet.tasks:
            st.markdown(f"**{pet.name}** ({pet.species})")
            st.table([
                {
                    "title": t.title,
                    "duration_min": t.duration_minutes,
                    "priority": t.priority,
                    "required": t.required,
                    "status": t.status,
                }
                for t in pet.tasks
            ])

st.divider()

# ---------------------------------------------------------------------------
# Step 4 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("4. Build Schedule")

if "owner" not in st.session_state or not st.session_state.owner.pets:
    st.info("Add at least one pet with tasks first.")
else:
    pets = st.session_state.owner.pets
    pets_with_tasks = [p for p in pets if p.tasks]

    if not pets_with_tasks:
        st.info("Add tasks to at least one pet before generating a schedule.")
    else:
        pet_options = [p.name for p in pets_with_tasks] + (
            ["All pets"] if len(pets_with_tasks) > 1 else []
        )
        schedule_target = st.selectbox("Generate schedule for", pet_options)

        if st.button("Generate schedule"):
            owner = st.session_state.owner

            if schedule_target == "All pets":
                # Each pet gets a proportional share — owner.pets contains all pets
                total_tasks = sum(len(p.tasks) for p in pets_with_tasks)
                for pet in pets_with_tasks:
                    scheduler = Scheduler(owner=owner, pet=pet)
                    plan = scheduler.generate_plan()
                    allocated = int(owner.available_minutes * len(pet.tasks) / total_tasks)
                    st.markdown(f"### {pet.name} ({pet.species})")
                    st.success(f"{plan.total_minutes_used} min used out of {allocated} min allocated")
                    st.text(plan.explanation)
                    if plan.selected_tasks:
                        st.table([
                            {"title": t.title, "duration_min": t.duration_minutes, "priority": t.priority}
                            for t in plan.selected_tasks
                        ])
            else:
                # Single pet selected — give it the full available_minutes
                pet = next(p for p in pets_with_tasks if p.name == schedule_target)
                single_pet_owner = Owner(
                    owner.name,
                    owner.available_minutes,
                    buffer_minutes=owner.buffer_minutes,
                    pets=[pet],
                )
                scheduler = Scheduler(owner=single_pet_owner, pet=pet)
                plan = scheduler.generate_plan()
                st.success(f"Schedule for {pet.name} — {plan.total_minutes_used} min used.")
                st.text(plan.explanation)
                if plan.selected_tasks:
                    st.table([
                        {"title": t.title, "duration_min": t.duration_minutes, "priority": t.priority}
                        for t in plan.selected_tasks
                    ])
