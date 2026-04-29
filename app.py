import os
from typing import Optional
import streamlit as st
from tabulate import tabulate
from pawpal_system import Owner, Pet, Task, Scheduler
from ai_advisor import PawPalAgent

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_SPECIES_EMOJI = {"dog": "🐕", "cat": "🐱", "other": "🐾"}
_PRIORITY_BG = {"high": "#ffe5e5", "medium": "#fff9e6", "low": "#eafaea"}


def _colored_table(rows: list[dict], priority_key: str = "_priority") -> str:
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


def _render_plan(plan, allocated_minutes: Optional[int] = None) -> None:
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
    with st.expander("Full explanation"):
        st.text(plan.explanation)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Global styles
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #11998e 100%);
    background-attachment: fixed;
}

/* ── Main content card ── */
.block-container {
    background: rgba(255, 255, 255, 0.97);
    border-radius: 20px;
    padding: 2rem 2.5rem !important;
    margin-top: 1rem;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2d1b69 0%, #11998e 100%) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown {
    color: rgba(255,255,255,0.9) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: white !important;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input {
    background: white !important;
    color: #2d1b69 !important;
    border-color: rgba(255,255,255,0.5) !important;
    border-radius: 8px !important;
    caret-color: #2d1b69 !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] input::placeholder {
    color: #aaa !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: white !important;
    color: #2d1b69 !important;
    border-color: rgba(255,255,255,0.5) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stSelectbox svg {
    fill: #2d1b69 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(90deg, #667eea, #764ba2) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
    padding: 0.45rem 1.4rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(102,126,234,0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102,126,234,0.55) !important;
    background: linear-gradient(90deg, #764ba2, #667eea) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Section headers ── */
h2 {
    color: #764ba2 !important;
    font-weight: 700 !important;
    border-left: 4px solid #667eea;
    padding-left: 12px;
    margin-top: 0.5rem !important;
}
h3 { color: #667eea !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #f5f7ff, #eef0ff) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    border: 1px solid #d5dbff !important;
    box-shadow: 0 2px 8px rgba(102,126,234,0.12) !important;
}

/* ── Divider ── */
hr {
    border: none !important;
    height: 2px !important;
    background: linear-gradient(90deg, #667eea, #764ba2, #11998e) !important;
    border-radius: 2px !important;
    opacity: 0.25 !important;
    margin: 1.5rem 0 !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    border-radius: 10px !important;
    border: 1px solid #e0e4ff !important;
}

/* ── Tables ── */
table {
    border-radius: 10px;
    overflow: hidden;
    width: 100%;
    border-collapse: collapse;
}
th {
    background: linear-gradient(90deg, #667eea, #764ba2) !important;
    color: white !important;
    padding: 10px 14px !important;
    font-size: 0.85rem;
    letter-spacing: 0.4px;
}
td { padding: 8px 14px !important; font-size: 0.9rem; }

/* ── Section card wrapper ── */
.section-card {
    background: #f8f9ff;
    border-radius: 14px;
    border: 1px solid #e0e4ff;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 12px rgba(102,126,234,0.08);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — Owner & Pets
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🐾 PawPal+")
    st.markdown("---")

    # ── Owner ──
    st.markdown("### 👤 Caretaker")
    owner_name = st.text_input("Name", value="Jordan", key="owner_name_input")
    available_minutes = st.number_input(
        "Available minutes today", min_value=1, max_value=1440, value=120
    )
    buffer_minutes = st.number_input(
        "Buffer between tasks (min)", min_value=0, max_value=60, value=5,
        help="Rest/travel time between tasks",
    )
    if st.button("Save owner"):
        st.session_state.owner = Owner(
            owner_name, int(available_minutes), buffer_minutes=int(buffer_minutes)
        )
        st.success(f"Saved {owner_name}!")

    if "owner" in st.session_state:
        o = st.session_state.owner
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.15);border-radius:8px;"
            f"padding:8px 12px;margin-top:6px;color:white;font-size:0.85rem'>"
            f"⏱ {o.available_minutes} min &nbsp;|&nbsp; 🔄 {o.buffer_minutes} min buffer</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Pets ──
    st.markdown("### 🐾 Pets")
    if "owner" not in st.session_state:
        st.caption("Save an owner first.")
    else:
        col_pname, col_species = st.columns(2)
        with col_pname:
            pet_name = st.text_input("Pet name", value="Mochi", key="pet_name_input")
        with col_species:
            species = st.selectbox("Species", ["dog", "cat", "other"], key="species_input")

        if st.button("Add pet"):
            new_pet = Pet(pet_name, species)
            st.session_state.owner.pets.append(new_pet)
            st.success(f"{pet_name} added!")

        if st.session_state.owner.pets:
            for p in st.session_state.owner.pets:
                icon = _SPECIES_EMOJI.get(p.species, "🐾")
                st.markdown(
                    f"<div style='background:rgba(255,255,255,0.15);border-radius:8px;"
                    f"padding:6px 10px;margin:4px 0;color:white;font-size:0.88rem'>"
                    f"{icon} <b>{p.name}</b> &nbsp;·&nbsp; {p.species} &nbsp;·&nbsp; {len(p.tasks)} tasks</div>",
                    unsafe_allow_html=True,
                )
            remove_pet_name = st.selectbox(
                "Remove pet", [p.name for p in st.session_state.owner.pets],
                key="remove_pet_select",
            )
            if st.button("Remove 🗑️"):
                st.session_state.owner.pets = [
                    p for p in st.session_state.owner.pets if p.name != remove_pet_name
                ]
                st.rerun()

# ---------------------------------------------------------------------------
# Main — Header
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='color:#764ba2;font-size:2.4rem;margin-bottom:0'>🐾 PawPal+</h1>"
    "<p style='color:#888;margin-top:4px;font-size:1rem'>"
    "AI-powered daily care scheduling for your pets</p>",
    unsafe_allow_html=True,
)
st.divider()

# ---------------------------------------------------------------------------
# Step 1 — Tasks
# ---------------------------------------------------------------------------
st.subheader("📋 What Needs to Get Done?")

if "owner" not in st.session_state or not st.session_state.owner.pets:
    st.info("Set up an owner and add at least one pet in the sidebar to get started.")
else:
    pets = st.session_state.owner.pets
    pet_names = [p.name for p in pets]

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
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
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        required = st.checkbox("Required", value=False, help="Always include regardless of time pressure")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Add task ＋"):
        duplicate = any(
            t.title.lower() == task_title.strip().lower() and t.status == "pending"
            for t in target_pet.tasks
        )
        if duplicate:
            st.warning(f"'{task_title}' is already pending for {target_pet.name}.")
        else:
            target_pet.add_task(Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                required=required,
            ))
    st.markdown("</div>", unsafe_allow_html=True)

    ai_titles = st.session_state.get("ai_added_task_titles", set())
    for pet in pets:
        if pet.tasks:
            icon = _SPECIES_EMOJI.get(pet.species, "🐾")
            st.markdown(f"**{icon} {pet.name}** ({pet.species})")
            sorted_tasks = sorted(pet.tasks, key=lambda t: (PRIORITY_ORDER[t.priority], t.duration_minutes))
            st.markdown(_colored_table([
                {
                    "": _task_emoji(t.title),
                    "title": ("🤖 " if (pet.name, t.title) in ai_titles else "") + t.title,
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
# Step 2 — AI Care Agent
# ---------------------------------------------------------------------------
st.subheader("🤖 AI Care Agent")
st.markdown(
    "Let Claude analyze your pets' schedules, fill care gaps, and build optimized plans automatically. "
    "Tasks added by the agent are marked with 🤖 above."
)

if "owner" not in st.session_state or not st.session_state.owner.pets:
    st.info("Add at least one pet in the sidebar first.")
elif not any(p.tasks for p in st.session_state.owner.pets):
    st.info("Add tasks to at least one pet before running the AI agent.")
elif not os.environ.get("ANTHROPIC_API_KEY"):
    st.warning(
        "Set the **ANTHROPIC_API_KEY** environment variable to enable the AI Care Agent.\n\n"
        "`export ANTHROPIC_API_KEY=sk-ant-...` then restart the app."
    )
else:
    if st.button("🤖 Run AI Care Agent"):
        with st.status("🤖 Claude is analyzing your pets' care schedule…", expanded=True) as status:
            try:
                agent = PawPalAgent(st.session_state.owner)

                def on_step(kind, message):
                    icon = "⚙️" if kind == "call" else "↳"
                    st.write(f"{icon} {message}")

                result = agent.run(on_step=on_step)
                status.update(label="✅ Analysis complete!", state="complete", expanded=False)

                ai_titles = {(item["pet"], item["title"]) for item in result["added_tasks"]}
                existing = st.session_state.get("ai_added_task_titles", set())
                st.session_state.ai_added_task_titles = existing | ai_titles

                if result["plans"]:
                    owner = st.session_state.owner
                    pets_in_plan = [p for p in owner.pets if p.name in result["plans"]]
                    total_tasks = sum(len(p.tasks) for p in pets_in_plan)
                    all_plans, running_offset = [], 0
                    for pet in pets_in_plan:
                        plan = result["plans"][pet.name]
                        plan.start_offset = running_offset
                        allocated = int(owner.available_minutes * len(pet.tasks) / max(total_tasks, 1))
                        all_plans.append((plan, allocated))
                        slots = plan.get_time_slots()
                        if slots:
                            running_offset = slots[-1][2] + owner.buffer_minutes
                    conflicts = Scheduler.detect_conflicts(*[p for p, _ in all_plans])
                    st.session_state.schedule = {
                        "type": "all",
                        "plans": all_plans,
                        "conflicts": conflicts,
                        "ai_generated": True,
                    }
                st.session_state.ai_result = result

            except Exception as exc:
                status.update(label="❌ Agent error", state="error", expanded=True)
                st.error(f"AI agent error: {exc}")

    if "ai_result" in st.session_state:
        result = st.session_state.ai_result
        if result["added_tasks"]:
            st.success(f"✨ Agent added **{len(result['added_tasks'])} task(s)** to fill care gaps:")
            for item in result["added_tasks"]:
                badge = "🔒 " if item.get("required") else ""
                st.markdown(
                    f"- **{item['pet']}**: {badge}{item['title']} "
                    f"({item['priority']} priority, {item['duration_minutes']} min)"
                )
        else:
            st.info("No gaps found — your pets' schedules are already well-rounded!")

        if result.get("summary"):
            with st.expander("AI agent analysis"):
                st.markdown(result["summary"])

        st.caption("Scroll down to see the AI-generated schedule ↓")

st.divider()

# ---------------------------------------------------------------------------
# Step 3 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("🗓️ Daily Schedule")

if "owner" not in st.session_state or not st.session_state.owner.pets:
    st.info("Add at least one pet with tasks first.")
else:
    pets = st.session_state.owner.pets
    pets_with_tasks = [p for p in pets if p.tasks]

    if not pets_with_tasks:
        st.info("Add tasks to at least one pet before generating a schedule.")
    else:
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            pet_options = [p.name for p in pets_with_tasks] + (
                ["All pets"] if len(pets_with_tasks) > 1 else []
            )
            schedule_target = st.selectbox("Generate schedule for", pet_options)
        with col_btn:
            st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
            gen_clicked = st.button("Generate 🗓️")
            st.markdown("</div>", unsafe_allow_html=True)

        if gen_clicked:
            owner = st.session_state.owner
            for pet in owner.pets:
                for task in pet.tasks:
                    task.status = "pending"

            if schedule_target == "All pets":
                total_tasks = sum(len(p.tasks) for p in pets_with_tasks)
                all_plans, running_offset = [], 0
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
                    owner.name, owner.available_minutes,
                    buffer_minutes=owner.buffer_minutes, pets=[pet],
                )
                plan = Scheduler(owner=single_pet_owner, pet=pet).generate_plan()
                st.session_state.schedule = {"type": "single", "pet": pet, "plan": plan}

        if "schedule" in st.session_state:
            sched = st.session_state.schedule
            if sched.get("ai_generated"):
                st.info("🤖 This schedule was built by the AI Care Agent and includes AI-recommended tasks.")
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
# Step 4 — Mark tasks complete
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
        col_pick, col_done = st.columns([4, 1])
        with col_pick:
            options = {
                f"{_SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name} — {_task_emoji(task.title)} {task.title}": (pet, task)
                for pet, task in all_pending
            }
            chosen = st.selectbox("Which task did you finish?", list(options.keys()), key="complete_task_select")
        with col_done:
            st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
            if st.button("Mark done ✅"):
                chosen_pet, chosen_task = options[chosen]
                chosen_pet.complete_task(chosen_task)
                st.success(f"✅ '{chosen_task.title}' marked complete for {chosen_pet.name}!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
