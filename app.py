import streamlit as st
from tabulate import tabulate
from pawpal_system import Owner, Pet, Task, Scheduler

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

_SPECIES_EMOJI = {"dog": "🐕", "cat": "🐱", "other": "🐾"}

_PRIORITY_BG = {"high": "#ffe5e5", "medium": "#fff9e6", "low": "#eafaea"}


def _colored_table(rows: list[dict], priority_key: str = "_priority") -> str:
    """Use tabulate to build an HTML table, then inject per-row background colors by priority."""
    priorities = [r.get(priority_key, "") for r in rows]
    visible = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    base_html = tabulate(visible, headers="keys", tablefmt="html")
    lines = base_html.splitlines()
    result, row_idx, in_tbody = [], 0, False
    for line in lines:
        if "<tbody>" in line:
            in_tbody = True
        if in_tbody and "<tr>" in line and row_idx < len(priorities):
            bg = _PRIORITY_BG.get(priorities[row_idx], "#ffffff")
            line = line.replace("<tr>", f"<tr style='background-color:{bg}'>", 1)
            row_idx += 1
        result.append(line)
    return "\n".join(result)

_TASK_KEYWORDS = [
    ({"walk", "stroll", "run", "jog"},          "🦮"),
    ({"feed", "food", "meal", "treat", "water"}, "🍽️"),
    ({"groom", "brush", "bath", "wash", "nail"}, "✂️"),
    ({"play", "fetch", "toy", "game"},           "🎾"),
    ({"medicine", "med", "pill", "dose", "vet", "checkup"}, "💊"),
    ({"litter", "clean", "scoop", "poop"},       "🧹"),
    ({"train", "training", "sit", "stay"},       "🎓"),
    ({"cuddle", "snuggle", "pet", "love"},       "🫶"),
]


def _task_emoji(title: str) -> str:
    lower = title.lower()
    for keywords, emoji in _TASK_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return emoji
    return "📋"


def _priority_badge(priority: str) -> str:
    icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    return f"{icons.get(priority, '')} {priority}"


def _status_badge(status: str) -> str:
    return "✅ complete" if status == "complete" else "⏳ pending"


def _render_plan(plan, allocated_minutes: int | None = None) -> None:
    """Render a Plan's time slots and summary using Streamlit components."""
    budget = allocated_minutes if allocated_minutes is not None else plan.owner.available_minutes

    col_used, col_budget, col_tasks = st.columns(3)
    col_used.metric("Minutes used", plan.total_minutes_used)
    col_budget.metric("Budget", budget)
    col_tasks.metric("Tasks scheduled", len(plan.selected_tasks))

    slots = plan.get_time_slots()
    if slots:
        st.markdown(_colored_table([
            {
                "": _task_emoji(t.title),
                "task": t.title,
                "time": f"{start}–{end} min",
                "duration": f"{t.duration_minutes} min",
                "priority": _priority_badge(t.priority),
                "required": "🔒" if t.required else "",
                "_priority": t.priority,
            }
            for t, start, end in slots
        ]), unsafe_allow_html=True)
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
### Your pet's day, perfectly planned! 🐕🐱

Tails are wagging and paws are ready — let's build the ultimate care schedule for your furry (or not-so-furry) family members.

Tell us about your pets, drop in their tasks, and PawPal+ will figure out the best way to fit everything into your day. No more forgotten walks or missed feedings! 🦴🐟
"""
)

st.divider()

# ---------------------------------------------------------------------------
# Step 1 — Owner
# ---------------------------------------------------------------------------
st.subheader("👤 Who's the Caretaker?")

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
st.subheader("🐾 Meet the Pets")

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
            {
                "": _SPECIES_EMOJI.get(p.species, "🐾"),
                "name": p.name,
                "species": p.species,
                "tasks": len(p.tasks),
            }
            for p in st.session_state.owner.pets
        ])
        remove_pet_name = st.selectbox(
            "Remove a pet", [p.name for p in st.session_state.owner.pets], key="remove_pet_select"
        )
        if st.button("Remove pet 🗑️"):
            st.session_state.owner.pets = [
                p for p in st.session_state.owner.pets if p.name != remove_pet_name
            ]
            st.rerun()
    else:
        st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Step 3 — Tasks
# ---------------------------------------------------------------------------
st.subheader("📋 What Needs to Get Done?")

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
        duplicate = any(
            t.title.lower() == task_title.strip().lower() and t.status == "pending"
            for t in target_pet.tasks
        )
        if duplicate:
            st.warning(f"'{task_title}' is already a pending task for {target_pet.name}. Skipping.")
        else:
            task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                required=required,
            )
            target_pet.add_task(task)

    for pet in pets:
        if pet.tasks:
            icon = _SPECIES_EMOJI.get(pet.species, "🐾")
            st.markdown(f"**{icon} {pet.name}** ({pet.species})")
            sorted_tasks = sorted(pet.tasks, key=lambda t: (PRIORITY_ORDER[t.priority], t.duration_minutes))
            st.markdown(_colored_table([
                {
                    "": _task_emoji(t.title),
                    "title": t.title,
                    "priority": _priority_badge(t.priority),
                    "duration": f"{t.duration_minutes} min",
                    "required": "🔒" if t.required else "",
                    "status": _status_badge(t.status),
                    "_priority": t.priority,
                }
                for t in sorted_tasks
            ]), unsafe_allow_html=True)

    all_tasks = [(pet, task) for pet in pets for task in pet.tasks]
    if all_tasks:
        st.markdown("**🗑️ Remove a task**")
        task_options = {
            f"{_SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name} — {_task_emoji(task.title)} {task.title}": (pet, task)
            for pet, task in all_tasks
        }
        remove_choice = st.selectbox("Select task to remove", list(task_options.keys()), key="remove_task_select")
        if st.button("Remove task 🗑️"):
            chosen_pet, chosen_task = task_options[remove_choice]
            chosen_pet.tasks.remove(chosen_task)
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Step 4 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("🗓️ Let's Build the Perfect Day!")

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
            for pet in owner.pets:
                for task in pet.tasks:
                    task.status = "pending"

            if schedule_target == "All pets":
                total_tasks = sum(len(p.tasks) for p in pets_with_tasks)
                all_plans = []
                running_offset = 0
                for pet in pets_with_tasks:
                    scheduler = Scheduler(owner=owner, pet=pet)
                    plan = scheduler.generate_plan()
                    plan.start_offset = running_offset
                    allocated = int(owner.available_minutes * len(pet.tasks) / total_tasks)
                    all_plans.append((plan, allocated))
                    slots = plan.get_time_slots()
                    if slots:
                        running_offset = slots[-1][2] + owner.buffer_minutes
                conflicts = Scheduler.detect_conflicts(*[p for p, _ in all_plans])
                st.session_state.schedule = {"type": "all", "plans": all_plans, "conflicts": conflicts}
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
                st.session_state.schedule = {"type": "single", "pet": pet, "plan": plan}

        # Always render the saved schedule
        if "schedule" in st.session_state:
            sched = st.session_state.schedule
            if sched["type"] == "all":
                for plan, allocated in sched["plans"]:
                    st.markdown(f"### {_SPECIES_EMOJI.get(plan.pet.species, '🐾')} {plan.pet.name} ({plan.pet.species})")
                    _render_plan(plan, allocated_minutes=allocated)
                if sched["conflicts"]:
                    st.markdown("---")
                    st.markdown("#### Scheduling conflicts detected")
                    for msg in sched["conflicts"]:
                        clean = msg.removeprefix("WARNING: ")
                        st.warning(
                            f"**Overlap:** {clean}\n\n"
                            "_Two pets have tasks scheduled at the same time. "
                            "Consider staggering start times or reducing one task's duration._"
                        )
                else:
                    st.success("No scheduling conflicts across pets.")
            else:
                st.success(f"Schedule generated for **{sched['pet'].name}**.")
                _render_plan(sched["plan"])

st.divider()

# ---------------------------------------------------------------------------
# Step 5 — Mark tasks complete
# ---------------------------------------------------------------------------
st.subheader("☑️ Done for the Day?")

if "owner" not in st.session_state or not st.session_state.owner.pets:
    st.info("Add pets and generate a schedule first.")
else:
    all_pending = [
        (pet, task)
        for pet in st.session_state.owner.pets
        for task in pet.tasks
        if task.status == "pending"
    ]
    if not all_pending:
        st.success("🎉 All tasks are complete! Great job taking care of your pets today!")
    else:
        options = {
            f"{_SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name} — {_task_emoji(task.title)} {task.title}": (pet, task)
            for pet, task in all_pending
        }
        chosen = st.selectbox("Which task did you finish?", list(options.keys()), key="complete_task_select")
        if st.button("Mark complete ✅"):
            chosen_pet, chosen_task = options[chosen]
            chosen_pet.complete_task(chosen_task)
            st.success(f"✅ '{chosen_task.title}' marked complete for {chosen_pet.name}!")
            st.rerun()
