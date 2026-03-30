from pawpal_system import Owner, Pet, Task, Scheduler

# Create owner
owner = Owner(name="Alex", available_minutes=90)

# Create pets
buddy = Pet(name="Buddy", species="dog")
whiskers = Pet(name="Whiskers", species="cat")

# Add tasks to Buddy (dog)
buddy.tasks.append(Task(title="Morning walk",        duration_minutes=30, priority="high",   species="dog"))
buddy.tasks.append(Task(title="Feeding",             duration_minutes=10, priority="high"))
buddy.tasks.append(Task(title="Grooming / brush",    duration_minutes=20, priority="medium"))
buddy.tasks.append(Task(title="Playtime fetch",      duration_minutes=25, priority="low",    species="dog"))

# Add tasks to Whiskers (cat)
whiskers.tasks.append(Task(title="Feeding",          duration_minutes=10, priority="high"))
whiskers.tasks.append(Task(title="Litter box clean", duration_minutes=15, priority="high",   species="cat"))
whiskers.tasks.append(Task(title="Interactive play", duration_minutes=20, priority="medium", species="cat"))
whiskers.tasks.append(Task(title="Brushing",         duration_minutes=10, priority="low"))

# Register pets with owner
owner.pets.extend([buddy, whiskers])

# Generate schedules
buddy_plan    = Scheduler(owner=owner, pet=buddy).generate_plan()
whiskers_plan = Scheduler(owner=owner, pet=whiskers).generate_plan()

# Print Today's Schedule
print("=" * 50)
print("         TODAY'S SCHEDULE — PawPal+")
print("=" * 50)

for plan in (buddy_plan, whiskers_plan):
    print()
    print(plan.explanation)
    print("-" * 50)
