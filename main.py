"""
PawPal+ CLI Demo

Demonstrates core functionality in the terminal before connecting to Streamlit.
"""

from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency
from datetime import datetime


def main():
    # Create owner
    owner = Owner(name="Jordan", available_time_minutes=120)
    print(f"Owner: {owner.name} ({owner.available_time_minutes} min/day)")

    # Create pets
    dog = Pet(name="Max", species="dog", age=3)
    dog.add_special_need("joint medication")
    owner.add_pet(dog)

    cat = Pet(name="Luna", species="cat", age=2)
    cat.add_special_need("indoor only")
    owner.add_pet(cat)

    print(f"Pets: {dog.name} ({dog.species}), {cat.name} ({cat.species})")

    # Set up scheduler
    scheduler = Scheduler(owner)

    # Add tasks with different priorities and times
    tasks = [
        Task("Morning walk", 30, 5, TaskType.WALK, dog, scheduled_time="07:00"),
        Task("Dog medication", 5, 5, TaskType.MEDICATION, dog, scheduled_time="07:30"),
        Task("Feed dog", 10, 4, TaskType.FEED, dog, scheduled_time="08:00"),
        Task("Feed cat", 10, 4, TaskType.FEED, cat, scheduled_time="08:00"),
        Task("Play session", 25, 3, TaskType.PLAYTIME, dog),
        Task("Cat enrichment", 20, 3, TaskType.ENRICHMENT, cat),
        Task("Evening walk", 45, 4, TaskType.WALK, dog, scheduled_time="17:00"),
        Task("Grooming", 60, 2, TaskType.GROOMING, dog),
    ]

    for t in tasks:
        scheduler.add_task(t)

    print(f"\nAdded {len(tasks)} tasks")

    # Show sorting by time
    print("\n--- Tasks sorted by time ---")
    for t in scheduler.sort_by_time():
        time_str = t.scheduled_time or "unscheduled"
        print(f"  [{time_str}] {t.name} ({t.pet.name}) - {t.duration_minutes}min, priority {t.priority}")

    # Check for conflicts
    warnings = scheduler.get_conflict_warnings()
    if warnings:
        print(f"\n{warnings}")

    # Filter by pet
    print(f"\n--- {dog.name}'s tasks ---")
    for t in scheduler.get_tasks_by_pet(dog):
        print(f"  {t.name} - {t.duration_minutes}min")

    # Generate daily plan
    print("\n--- Today's Schedule ---")
    plan = scheduler.generate_daily_plan()
    for i, t in enumerate(plan, 1):
        print(f"  {i}. {t.name} ({t.pet.name}) - {t.duration_minutes}min, priority {t.priority}")

    print(f"\nTotal scheduled: {scheduler.get_total_scheduled_time()}min / {owner.available_time_minutes}min available")

    # Show explanation
    print("\n--- Scheduling Explanation ---")
    print(scheduler.explain_reasoning())

    # Mark a task complete
    print("\n--- Completing first task ---")
    plan[0].mark_complete()
    print(f"Completed: {plan[0].name}")
    print(f"Remaining incomplete: {len(scheduler.get_incomplete_tasks())}")


if __name__ == "__main__":
    main()
