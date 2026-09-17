"""
main.py

CLI demo script for PawPal+. Exercises the backend logic in pawpal_system.py
directly from the terminal, with no UI involved. Run with:

    python main.py

This is the "proof" that the system works before it gets connected to Streamlit,
and it demonstrates every algorithmic feature: sorting (with tasks added out of
order), time-budget filtering, conflict detection, recurring-task creation, the
next-available-slot finder (Challenge 1), and JSON persistence (Challenge 2).
"""

from datetime import date, time

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:  # Challenge 4 formatting is optional; degrade gracefully.
    HAS_TABULATE = False

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Priority,
    Frequency,
    Scheduler,
    save_to_json,
    load_from_json,
)

# Emoji per priority level, for Challenge 4 (professional formatting).
PRIORITY_EMOJI = {
    Priority.HIGH: "🔴",
    Priority.MEDIUM: "🟡",
    Priority.LOW: "🟢",
}


def build_demo_owner() -> Owner:
    """
    Create a sample Owner with two pets and tasks added deliberately OUT OF
    ORDER (by time), so the demo can prove that Scheduler.sort_by_time() /
    sort_by_priority_then_time() actually reorders them correctly.
    """
    owner = Owner(name="Jordan")

    biscuit = Pet(name="Biscuit", species="Golden Retriever")
    # Added out of order on purpose: 09:00, then 08:00, then 08:30.
    biscuit.add_task(
        Task(
            description="Heartworm medication",
            scheduled_time=time(9, 0),
            duration_minutes=5,
            priority=Priority.HIGH,
            frequency=Frequency.WEEKLY,
        )
    )
    biscuit.add_task(
        Task(
            description="Morning walk",
            scheduled_time=time(8, 0),
            duration_minutes=30,
            priority=Priority.HIGH,
            frequency=Frequency.DAILY,
        )
    )
    biscuit.add_task(
        Task(
            description="Breakfast",
            scheduled_time=time(8, 30),
            duration_minutes=10,
            priority=Priority.HIGH,
            frequency=Frequency.DAILY,
        )
    )

    mochi = Pet(name="Mochi", species="Cat")
    mochi.add_task(
        Task(
            description="Vet appointment check-in call",
            scheduled_time=time(14, 0),
            duration_minutes=15,
            priority=Priority.MEDIUM,
            frequency=Frequency.ONCE,
        )
    )
    # Deliberately scheduled at the SAME time as Biscuit's walk to demonstrate
    # cross-pet conflict detection.
    mochi.add_task(
        Task(
            description="Feeding",
            scheduled_time=time(8, 0),
            duration_minutes=10,
            priority=Priority.MEDIUM,
            frequency=Frequency.DAILY,
        )
    )
    mochi.add_task(
        Task(
            description="Litter box cleaning",
            scheduled_time=time(9, 30),
            duration_minutes=10,
            priority=Priority.LOW,
            frequency=Frequency.DAILY,
        )
    )

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


def print_plan(owner: Owner, minutes_available: int | None = None) -> None:
    """Print a formatted, prioritized daily schedule for the given owner."""
    scheduler = Scheduler(owner)
    result = scheduler.build_daily_plan(minutes_available=minutes_available)

    print(f"\n📋 Today's Schedule for {owner.name}'s pets")
    print("=" * 60)

    if not result["plan"]:
        print("No tasks scheduled.")
    elif HAS_TABULATE:
        rows = []
        for task in result["plan"]:
            pet = owner.find_pet_for_task(task)
            rows.append(
                [
                    task.scheduled_time.strftime("%I:%M %p"),
                    task.description,
                    pet.name if pet else "?",
                    f"{task.duration_minutes} min",
                    f"{PRIORITY_EMOJI[task.priority]} {task.priority}",
                ]
            )
        print(
            tabulate(
                rows,
                headers=["Time", "Task", "Pet", "Duration", "Priority"],
                tablefmt="simple",
            )
        )
    else:
        for task in result["plan"]:
            pet = owner.find_pet_for_task(task)
            print(f"  {PRIORITY_EMOJI[task.priority]} {task}  — {pet.name if pet else '?'}")

    if result["skipped"]:
        print("\n⏭️  Skipped (ran out of time budget):")
        for task in result["skipped"]:
            print(f"  {task}")

    if result["conflicts"]:
        print("\n⚠️  Scheduling conflicts detected:")
        for a, b in result["conflicts"]:
            print(f"  '{a.description}' overlaps with '{b.description}' at {a.scheduled_time.strftime('%I:%M %p')}")
    else:
        print("\n✅ No scheduling conflicts.")

    print("=" * 60)


def demo_recurring_task_creation(owner: Owner) -> None:
    """Demonstrate Phase 4 recurrence: completing a daily task auto-creates tomorrow's task."""
    scheduler = Scheduler(owner)
    biscuit = owner.find_pet("Biscuit")
    walk = next(t for t in biscuit.tasks if t.description == "Morning walk")

    print("\n🔁 Recurring task demo")
    print("=" * 60)
    print(f"Before: Biscuit has {biscuit.task_count()} tasks")
    new_task = scheduler.complete_task(walk)
    print(f"Marked '{walk.description}' complete (frequency: {walk.frequency.value})")
    if new_task:
        print(
            f"-> Auto-created next occurrence for {new_task.scheduled_date} "
            f"at {new_task.scheduled_time.strftime('%I:%M %p')}"
        )
    print(f"After:  Biscuit has {biscuit.task_count()} tasks")
    print("=" * 60)


def demo_next_available_slot(owner: Owner) -> None:
    """Demonstrate Challenge 1: find the next open slot for a new 20-minute task."""
    scheduler = Scheduler(owner)
    slot = scheduler.find_next_available_slot(duration_minutes=20, for_date=date.today())

    print("\n🕒 Next available 20-minute slot (Challenge 1)")
    print("=" * 60)
    if slot:
        print(f"Next available slot today: {slot.strftime('%I:%M %p')}")
    else:
        print("No slot available today.")
    print("=" * 60)


def demo_persistence(owner: Owner) -> None:
    """Demonstrate Challenge 2: save the owner's data to JSON, then reload it."""
    print("\n💾 Persistence demo (Challenge 2)")
    print("=" * 60)
    save_to_json(owner, "data.json")
    print("Saved owner + pets + tasks to data.json")

    reloaded = load_from_json("data.json")
    print(
        f"Reloaded owner '{reloaded.name}' with {len(reloaded.pets)} pets "
        f"and {len(reloaded.all_tasks())} total tasks"
    )
    print("=" * 60)


if __name__ == "__main__":
    demo_owner = build_demo_owner()
    print_plan(demo_owner)
    demo_recurring_task_creation(demo_owner)
    demo_next_available_slot(demo_owner)
    demo_persistence(demo_owner)
