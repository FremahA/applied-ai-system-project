import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _priority_badge(priority: str) -> str:
    icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    return f"{icons.get(priority, '')} {priority}"


def _render_plan(plan, allocated_minutes: int | None = None) -> None:
    """Render a Plan's time slots and summary using Streamlit components."""
    budget = allocated_minutes if allocated_minutes is not None else plan.owner.available_minutes

    col_used, col_budget, col_tasks = st.columns(3)
    col_used.metric("Minutes used", plan.total_minutes_used)
    col_budget.metric("Budget", budget)
    col_tasks.metric("Tasks scheduled", len(plan.selected_tasks))

    slots = plan.get_time_slots()
    if slots:
        st.table([
            {
                "start (min)": start,
                "end (min)": end,
                "task": t.title,
                "priority": _priority_badge(t.priority),
                "duration (min)": t.duration_minutes,
                "required": "✓" if t.required else "",
            }
            for t, start, end in slots
        ])
    else:
        st.info("No tasks could be scheduled within the time budget.")

    # Skipped / excluded tasks pulled from the explanation text are already
    # in plan.explanation — show it collapsed so it's available but not loud.
    with st.expander("Full explanation"):
        st.text(plan.explanation)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.


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
            sorted_tasks = sorted(pet.tasks, key=lambda t: (PRIORITY_ORDER[t.priority], t.duration_minutes))
            st.table([
                {
                    "title": t.title,
                    "priority": _priority_badge(t.priority),
                    "duration (min)": t.duration_minutes,
                    "required": "✓" if t.required else "",
                    "status": t.status,
                }
                for t in sorted_tasks
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
                total_tasks = sum(len(p.tasks) for p in pets_with_tasks)
                all_plans = []
                for pet in pets_with_tasks:
                    scheduler = Scheduler(owner=owner, pet=pet)
                    plan = scheduler.generate_plan()
                    allocated = int(owner.available_minutes * len(pet.tasks) / total_tasks)
                    all_plans.append(plan)
                    st.markdown(f"### {pet.name} ({pet.species})")
                    _render_plan(plan, allocated_minutes=allocated)

                # Surface any cross-pet time-slot conflicts
                conflicts = Scheduler.detect_conflicts(*all_plans)
                if conflicts:
                    st.markdown("---")
                    st.markdown("#### Scheduling conflicts detected")
                    for msg in conflicts:
                        # Strip leading "WARNING: " prefix for cleaner display
                        clean = msg.removeprefix("WARNING: ")
                        st.warning(
                            f"**Overlap:** {clean}\n\n"
                            "_Two pets have tasks scheduled at the same time. "
                            "Consider staggering start times or reducing one task's duration._"
                        )
                else:
                    st.success("No scheduling conflicts across pets.")
            else:
                # Single pet — give it the full available_minutes
                pet = next(p for p in pets_with_tasks if p.name == schedule_target)
                single_pet_owner = Owner(
                    owner.name,
                    owner.available_minutes,
                    buffer_minutes=owner.buffer_minutes,
                    pets=[pet],
                )
                scheduler = Scheduler(owner=single_pet_owner, pet=pet)
                plan = scheduler.generate_plan()
                st.success(f"Schedule generated for **{pet.name}**.")
                _render_plan(plan)
