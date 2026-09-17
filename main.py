"""
main.py

CLI demo script for PawPal+. Exercises the backend logic in pawpal_system.py
directly from the terminal, with no UI involved. Run with:

    python main.py

This is the "proof" that the system works before it gets connected to Streamlit.
"""

from datetime import time

from pawpal_system import Owner, Pet, Task, Priority, Frequency, Scheduler


def build_demo_owner() -> Owner:
    """Create a sample Owner with two pets and several tasks for the demo."""
    owner = Owner(name="Jordan")

    biscuit = Pet(name="Biscuit", species="Golden Retriever")
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
    biscuit.add_task(
        Task(
            description="Heartworm medication",
            scheduled_time=time(9, 0),
            duration_minutes=5,
            priority=Priority.HIGH,
            frequency=Frequency.WEEKLY,
        )
    )

    mochi = Pet(name="Mochi", species="Cat")
    mochi.add_task(
        Task(
            description="Feeding",
            scheduled_time=time(8, 15),
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
    mochi.add_task(
        Task(
            description="Vet appointment check-in call",
            scheduled_time=time(14, 0),
            duration_minutes=15,
            priority=Priority.MEDIUM,
            frequency=Frequency.ONCE,
        )
    )

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


def print_plan(owner: Owner, minutes_available: int | None = None) -> None:
    """Print a formatted daily schedule for the given owner."""
    scheduler = Scheduler(owner)
    result = scheduler.build_daily_plan(minutes_available=minutes_available)

    print(f"\n📋 Today's Schedule for {owner.name}'s pets")
    print("=" * 50)

    if not result["plan"]:
        print("No tasks scheduled.")
    for task in result["plan"]:
        pet_name = next(
            (pet.name for pet in owner.pets if task in pet.tasks), "Unknown"
        )
        print(f"  {task}  — {pet_name}")

    if result["skipped"]:
        print("\n⏭️  Skipped (ran out of time budget):")
        for task in result["skipped"]:
            print(f"  {task}")

    if result["conflicts"]:
        print("\n⚠️  Scheduling conflicts detected:")
        for a, b in result["conflicts"]:
            print(f"  {a.description} overlaps with {b.description}")
    else:
        print("\n✅ No scheduling conflicts.")

    print("=" * 50)


if __name__ == "__main__":
    demo_owner = build_demo_owner()
    print_plan(demo_owner)
