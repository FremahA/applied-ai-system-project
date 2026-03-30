from pawpal_system import Owner, Pet, Task, Scheduler

# Create owner — buffer_minutes adds rest/travel time between tasks (#8)
owner = Owner(name="Alex", available_minutes=90, buffer_minutes=5)

# Create pets
buddy = Pet(name="Buddy", species="dog")
whiskers = Pet(name="Whiskers", species="cat")

# Add tasks OUT OF ORDER to demonstrate auto-sorting by duration_minutes
buddy.add_task(Task(title="Playtime fetch",      duration_minutes=25, priority="low",    species="dog"))
buddy.add_task(Task(title="Morning walk",        duration_minutes=30, priority="high",   species="dog"))
buddy.add_task(Task(title="Feeding",             duration_minutes=10, priority="high",   required=True))
buddy.add_task(Task(title="Grooming / brush",    duration_minutes=20, priority="medium"))

whiskers.add_task(Task(title="Interactive play", duration_minutes=20, priority="medium", species="cat"))
whiskers.add_task(Task(title="Brushing",         duration_minutes=10, priority="low"))
whiskers.add_task(Task(title="Feeding",          duration_minutes=10, priority="high",   required=True))
whiskers.add_task(Task(title="Litter box clean", duration_minutes=15, priority="high",   species="cat"))

# Register pets with owner
owner.pets.extend([buddy, whiskers])

# --- Demonstrate sorting ---
print("=" * 50)
print("       TASKS SORTED BY DURATION (shortest first)")
print("=" * 50)

for pet in (buddy, whiskers):
    print(f"\n{pet.name}'s tasks:")
    for t in pet.tasks:
        print(f"  {t.duration_minutes:>3} min — {t.title}")

# --- Demonstrate filter_tasks ---
print()
print("=" * 50)
print("         FILTERING BY COMPLETION STATUS")
print("=" * 50)

# Mark one task complete on each pet to show filtering
buddy.tasks[0].mark_complete()
whiskers.tasks[0].mark_complete()

for pet in (buddy, whiskers):
    pending  = pet.filter_tasks("pending")
    complete = pet.filter_tasks("complete")
    print(f"\n{pet.name} — pending ({len(pending)}): {[t.title for t in pending]}")
    print(f"{pet.name} — complete ({len(complete)}): {[t.title for t in complete]}")

# --- Demonstrate get_tasks_by_pet ---
print()
print("=" * 50)
print("         FILTERING BY PET NAME (via Owner)")
print("=" * 50)

for name in ("Buddy", "Whiskers", "Unknown"):
    tasks = owner.get_tasks_by_pet(name)
    print(f"\nTasks for '{name}': {[t.title for t in tasks] if tasks else 'pet not found'}")

# --- Generate and print schedules ---
buddy_plan    = Scheduler(owner=owner, pet=buddy).generate_plan()
whiskers_plan = Scheduler(owner=owner, pet=whiskers).generate_plan()

print()
print("=" * 50)
print("         TODAY'S SCHEDULE — PawPal+")
print("=" * 50)

for plan in (buddy_plan, whiskers_plan):
    print()
    print(plan.explanation)
    print("-" * 50)
