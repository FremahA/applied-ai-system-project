import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def test_mark_complete_changes_status_to_complete():
    task = Task(title="Morning walk", duration_minutes=20)
    task.mark_complete()
    assert task.status == "complete"


def test_add_task_increases_task_count_by_one():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Morning walk", duration_minutes=20)
    pet.add_task(task)
    assert len(pet.tasks) == 1
