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

# Priority display helpers
_PRIORITY_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}


def _priority_badge(p: str) -> str:
    return _PRIORITY_BADGE.get(p, p)


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
    st.success(f"Owner **{o.name}** created.")
    m1, m2 = st.columns(2)
    m1.metric("Available time", f"{o.available_minutes} min")
    m2.metric("Buffer between tasks", f"{o.buffer_minutes} min")

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
        st.success(f"Added **{pet_name}** ({species}).")

    if st.session_state.owner.pets:
        st.dataframe(
            [
                {"Name": p.name, "Species": p.species, "Tasks": len(p.tasks)}
                for p in st.session_state.owner.pets
            ],
            use_container_width=True,
            hide_index=True,
        )
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
        st.success(f"Added **{task_title}** to {target_pet.name}.")

    for pet in pets:
        if not pet.tasks:
            continue

        st.markdown(f"#### {pet.name} ({pet.species})")
        pending = pet.filter_tasks("pending")
        done = pet.filter_tasks("complete")

        c1, c2 = st.columns(2)
        c1.metric("Pending", len(pending))
        c2.metric("Completed", len(done))

        if pending:
            st.caption("Pending tasks — sorted by duration (shortest first)")
            st.dataframe(
                [
                    {
                        "Title": t.title,
                        "Duration (min)": t.duration_minutes,
                        "Priority": _priority_badge(t.priority),
                        "Required": "Yes" if t.required else "No",
                    }
                    for t in pending
                ],
                use_container_width=True,
                hide_index=True,
            )

        if done:
            with st.expander(f"View {len(done)} completed task(s)"):
                st.dataframe(
                    [
                        {"Title": t.title, "Duration (min)": t.duration_minutes}
                        for t in done
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

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
                    all_plans.append(plan)
                    allocated = int(owner.available_minutes * len(pet.tasks) / total_tasks)

                    st.markdown(f"#### {pet.name} ({pet.species})")

                    mu, ma = st.columns(2)
                    mu.metric("Time used", f"{plan.total_minutes_used} min")
                    ma.metric("Allocated", f"{allocated} min")

                    st.info(plan.explanation)

                    if plan.selected_tasks:
                        st.dataframe(
                            [
                                {
                                    "Title": t.title,
                                    "Start (min)": start,
                                    "End (min)": end,
                                    "Duration (min)": t.duration_minutes,
                                    "Priority": _priority_badge(t.priority),
                                    "Required": "Yes" if t.required else "No",
                                }
                                for t, start, end in plan.get_time_slots()
                            ],
                            use_container_width=True,
                            hide_index=True,
                        )

                st.divider()
                conflicts = Scheduler.detect_conflicts(*all_plans)
                if conflicts:
                    st.error(f"{len(conflicts)} scheduling conflict(s) detected — tasks below overlap in time.")
                    for c in conflicts:
                        with st.container(border=True):
                            col_a, col_mid, col_b = st.columns([5, 1, 5])
                            with col_a:
                                st.markdown(f"**{c.task_a.title}**")
                                st.caption(f"{c.pet_a} · {_priority_badge(c.task_a.priority)} · {c.task_a.duration_minutes} min")
                            with col_mid:
                                st.markdown("<div style='text-align:center;padding-top:8px'>⚠️</div>", unsafe_allow_html=True)
                            with col_b:
                                st.markdown(f"**{c.task_b.title}**")
                                st.caption(f"{c.pet_b} · {_priority_badge(c.task_b.priority)} · {c.task_b.duration_minutes} min")
                            st.caption(f"Overlap: {c.overlap_minutes} min — consider shortening one task, reducing it to optional, or increasing available time.")
                else:
                    st.success("No time-slot conflicts across pets.")

            else:
                pet = next(p for p in pets_with_tasks if p.name == schedule_target)
                single_pet_owner = Owner(
                    owner.name,
                    owner.available_minutes,
                    buffer_minutes=owner.buffer_minutes,
                    pets=[pet],
                )
                scheduler = Scheduler(owner=single_pet_owner, pet=pet)
                plan = scheduler.generate_plan()

                mu, ma = st.columns(2)
                mu.metric("Time used", f"{plan.total_minutes_used} min")
                ma.metric("Available", f"{owner.available_minutes} min")

                st.info(plan.explanation)

                if plan.selected_tasks:
                    st.dataframe(
                        [
                            {
                                "Title": t.title,
                                "Start (min)": start,
                                "End (min)": end,
                                "Duration (min)": t.duration_minutes,
                                "Priority": _priority_badge(t.priority),
                                "Required": "Yes" if t.required else "No",
                            }
                            for t, start, end in plan.get_time_slots()
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
