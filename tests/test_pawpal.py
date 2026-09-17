"""
tests/test_pawpal.py

Pytest suite for pawpal_system.py. Covers the two required "quick tests"
from Phase 2 (task completion, task addition) plus additional coverage of
the Phase 4 algorithmic layer: sorting, time-budget filtering, conflict
detection, and recurring-task handling.

Run with:
    python -m pytest
    python -m pytest -v          # verbose
    python -m pytest --cov       # with coverage (requires pytest-cov)
"""

from datetime import time

import pytest

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
)


# ---- fixtures -----------------------------------------------------

@pytest.fixture
def sample_task():
    return Task(
        description="Morning walk",
        scheduled_time=time(8, 0),
        duration_minutes=30,
        priority=Priority.HIGH,
        frequency=Frequency.DAILY,
    )


@pytest.fixture
def sample_pet():
    return Pet(name="Biscuit", species="Golden Retriever")


@pytest.fixture
def owner_with_two_pets():
    owner = Owner(name="Jordan")

    biscuit = Pet(name="Biscuit", species="Golden Retriever")
    biscuit.add_task(
        Task("Morning walk", time(8, 0), 30, Priority.HIGH, Frequency.DAILY)
    )
    biscuit.add_task(
        Task("Breakfast", time(8, 30), 10, Priority.HIGH, Frequency.DAILY)
    )

    mochi = Pet(name="Mochi", species="Cat")
    mochi.add_task(
        Task("Feeding", time(8, 15), 10, Priority.MEDIUM, Frequency.DAILY)
    )
    mochi.add_task(
        Task("Litter box", time(9, 0), 10, Priority.LOW, Frequency.DAILY)
    )

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


# ---- Phase 2 required tests -----------------------------------------------------

class TestTaskCompletion:
    """Required test: mark_complete() actually changes the task's status."""

    def test_mark_complete_changes_status(self, sample_task):
        assert sample_task.completed is False
        sample_task.mark_complete()
        assert sample_task.completed is True

    def test_mark_incomplete_resets_status(self, sample_task):
        sample_task.mark_complete()
        sample_task.mark_incomplete()
        assert sample_task.completed is False


class TestTaskAddition:
    """Required test: adding a task to a Pet increases that pet's task count."""

    def test_add_task_increases_count(self, sample_pet, sample_task):
        assert sample_pet.task_count() == 0
        sample_pet.add_task(sample_task)
        assert sample_pet.task_count() == 1

    def test_adding_multiple_tasks(self, sample_pet):
        sample_pet.add_task(Task("Walk", time(8, 0), 30))
        sample_pet.add_task(Task("Feed", time(9, 0), 10))
        assert sample_pet.task_count() == 2


# ---- Owner / retrieval -----------------------------------------------------

class TestOwner:
    def test_all_tasks_collects_across_pets(self, owner_with_two_pets):
        tasks = owner_with_two_pets.all_tasks()
        assert len(tasks) == 4

    def test_find_pet_by_name(self, owner_with_two_pets):
        pet = owner_with_two_pets.find_pet("Mochi")
        assert pet is not None
        assert pet.species == "Cat"

    def test_find_pet_missing_returns_none(self, owner_with_two_pets):
        assert owner_with_two_pets.find_pet("Nonexistent") is None


# ---- Phase 4: sorting -----------------------------------------------------

class TestSorting:
    def test_sort_by_priority_then_time(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        ordered = scheduler.sort_by_priority_then_time()
        # HIGH priority tasks should come before MEDIUM/LOW
        assert ordered[0].priority == Priority.HIGH
        assert ordered[1].priority == Priority.HIGH
        # within HIGH, earlier time comes first
        assert ordered[0].scheduled_time <= ordered[1].scheduled_time

    def test_sort_by_time(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        ordered = scheduler.sort_by_time()
        times = [t.scheduled_time for t in ordered]
        assert times == sorted(times)


# ---- Phase 4: filtering by time budget -----------------------------------------------------

class TestTimeBudgetFiltering:
    def test_filter_within_time_budget_selects_highest_priority_first(
        self, owner_with_two_pets
    ):
        scheduler = Scheduler(owner_with_two_pets)
        ordered = scheduler.sort_by_priority_then_time()
        selected, skipped = scheduler.filter_within_time_budget(
            ordered, minutes_available=40
        )
        total_selected_minutes = sum(t.duration_minutes for t in selected)
        assert total_selected_minutes <= 40
        # the two HIGH priority tasks (30 + 10 = 40 min) should be selected
        assert len(selected) == 2
        assert all(t.priority == Priority.HIGH for t in selected)
        assert len(skipped) == 2

    def test_filter_with_zero_budget_skips_everything(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        ordered = scheduler.sort_by_priority_then_time()
        selected, skipped = scheduler.filter_within_time_budget(ordered, 0)
        assert selected == []
        assert len(skipped) == 4


# ---- Phase 4: conflict detection -----------------------------------------------------

class TestConflictDetection:
    def test_detects_overlapping_tasks(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Walk", time(8, 0), duration_minutes=30))
        pet.add_task(Task("Vet call", time(8, 15), duration_minutes=15))  # overlaps
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        conflicts = scheduler.find_conflicts()
        assert len(conflicts) == 1

    def test_no_conflicts_for_sequential_tasks(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Walk", time(8, 0), duration_minutes=30))
        pet.add_task(Task("Feed", time(9, 0), duration_minutes=10))
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        assert scheduler.find_conflicts() == []

    def test_owner_with_two_pets_fixture_has_a_detectable_conflict(
        self, owner_with_two_pets
    ):
        # Sanity check: the shared fixture's 8:00-8:30 walk and 8:15 feeding
        # genuinely overlap, which is what main.py's demo output shows too.
        scheduler = Scheduler(owner_with_two_pets)
        conflicts = scheduler.find_conflicts()
        assert len(conflicts) == 1

    def test_back_to_back_tasks_do_not_conflict(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Walk", time(8, 0), duration_minutes=30))
        pet.add_task(Task("Feed", time(8, 30), duration_minutes=10))  # starts exactly when walk ends
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        assert scheduler.find_conflicts() == []


# ---- Phase 4: recurring tasks -----------------------------------------------------

class TestRecurringTasks:
    def test_reset_recurring_tasks_only_resets_daily(self, owner_with_two_pets):
        for task in owner_with_two_pets.all_tasks():
            task.mark_complete()

        scheduler = Scheduler(owner_with_two_pets)
        reset_count = scheduler.reset_recurring_tasks()

        assert reset_count == 4  # all 4 sample tasks are DAILY
        assert all(not t.completed for t in owner_with_two_pets.all_tasks())

    def test_once_tasks_are_not_reset(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        vet_visit = Task(
            "Vet checkup", time(14, 0), 30, Priority.MEDIUM, Frequency.ONCE
        )
        vet_visit.mark_complete()
        pet.add_task(vet_visit)
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        reset_count = scheduler.reset_recurring_tasks()

        assert reset_count == 0
        assert vet_visit.completed is True

    def test_recurring_tasks_filter(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        recurring = scheduler.recurring_tasks()
        assert len(recurring) == 4  # all sample tasks are DAILY


# ---- Full daily plan -----------------------------------------------------

class TestBuildDailyPlan:
    def test_build_daily_plan_without_budget_includes_all_incomplete(
        self, owner_with_two_pets
    ):
        scheduler = Scheduler(owner_with_two_pets)
        result = scheduler.build_daily_plan()
        assert len(result["plan"]) == 4
        assert result["skipped"] == []

    def test_completed_tasks_excluded_from_plan(self, owner_with_two_pets):
        owner_with_two_pets.pets[0].tasks[0].mark_complete()
        scheduler = Scheduler(owner_with_two_pets)
        result = scheduler.build_daily_plan()
        assert len(result["plan"]) == 3

    def test_build_daily_plan_respects_time_budget(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        result = scheduler.build_daily_plan(minutes_available=15)
        total_minutes = sum(t.duration_minutes for t in result["plan"])
        assert total_minutes <= 15
        assert len(result["skipped"]) > 0
