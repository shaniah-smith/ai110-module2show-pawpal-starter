"""
tests/test_pawpal.py

Pytest suite for pawpal_system.py. Covers:
  - The two required "quick tests" from Phase 2 (task completion, task addition)
  - The Phase 4/5 required algorithmic behaviors: sorting correctness,
    filtering (by time budget, completion status, and pet), conflict
    detection (duplicate/overlapping times), and recurrence (marking a
    daily/weekly task complete creates a new task for the next occurrence)
  - Stretch features: next-available-slot (Challenge 1) and JSON
    persistence (Challenge 2)

Run with:
    python -m pytest
    python -m pytest -v          # verbose
    python -m pytest --cov       # with coverage (requires pytest-cov)
"""

import json
import os
from datetime import date, time, timedelta

import pytest

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    load_from_json,
    save_to_json,
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

    def test_find_pet_for_task(self, owner_with_two_pets):
        mochi = owner_with_two_pets.find_pet("Mochi")
        feeding_task = mochi.tasks[0]
        assert owner_with_two_pets.find_pet_for_task(feeding_task) is mochi


# ---- Phase 4/5: sorting -----------------------------------------------------

class TestSorting:
    def test_sort_by_priority_then_time(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        ordered = scheduler.sort_by_priority_then_time()
        assert ordered[0].priority == Priority.HIGH
        assert ordered[1].priority == Priority.HIGH
        assert ordered[0].scheduled_time <= ordered[1].scheduled_time

    def test_sort_by_time_is_chronological(self):
        """Sorting correctness: tasks are returned in chronological order,
        even when added out of order."""
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Evening walk", time(18, 0), 20))
        pet.add_task(Task("Morning walk", time(7, 0), 20))
        pet.add_task(Task("Lunch", time(12, 0), 10))
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        ordered = scheduler.sort_by_time()
        times = [t.scheduled_time for t in ordered]
        assert times == sorted(times)
        assert ordered[0].description == "Morning walk"
        assert ordered[-1].description == "Evening walk"


# ---- Phase 4: filtering -----------------------------------------------------

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
        assert len(selected) == 2
        assert all(t.priority == Priority.HIGH for t in selected)
        assert len(skipped) == 2

    def test_filter_with_zero_budget_skips_everything(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        ordered = scheduler.sort_by_priority_then_time()
        selected, skipped = scheduler.filter_within_time_budget(ordered, 0)
        assert selected == []
        assert len(skipped) == 4


class TestFilterByPetAndStatus:
    def test_filter_by_pet_name(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        mochi_tasks = scheduler.filter_by_pet("Mochi")
        assert len(mochi_tasks) == 2
        assert all(t.description in ("Feeding", "Litter box") for t in mochi_tasks)

    def test_filter_by_pet_unknown_returns_empty(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        assert scheduler.filter_by_pet("Nonexistent") == []

    def test_filter_incomplete_excludes_completed(self, owner_with_two_pets):
        owner_with_two_pets.pets[0].tasks[0].mark_complete()
        scheduler = Scheduler(owner_with_two_pets)
        incomplete = scheduler.filter_incomplete()
        assert len(incomplete) == 3


# ---- Phase 4/5: conflict detection -----------------------------------------------------

class TestConflictDetection:
    def test_detects_overlapping_tasks(self):
        """Conflict detection: the Scheduler flags overlapping/duplicate times."""
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Walk", time(8, 0), duration_minutes=30))
        pet.add_task(Task("Vet call", time(8, 15), duration_minutes=15))  # overlaps
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        conflicts = scheduler.find_conflicts()
        assert len(conflicts) == 1

    def test_detects_exact_duplicate_times(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Walk", time(8, 0), duration_minutes=15))
        pet.add_task(Task("Meds", time(8, 0), duration_minutes=5))  # exact duplicate
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        assert len(scheduler.find_conflicts()) == 1

    def test_no_conflicts_for_sequential_tasks(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Walk", time(8, 0), duration_minutes=30))
        pet.add_task(Task("Feed", time(9, 0), duration_minutes=10))
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        assert scheduler.find_conflicts() == []

    def test_back_to_back_tasks_do_not_conflict(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        pet.add_task(Task("Walk", time(8, 0), duration_minutes=30))
        pet.add_task(Task("Feed", time(8, 30), duration_minutes=10))
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        assert scheduler.find_conflicts() == []

    def test_conflict_across_different_pets(self, owner_with_two_pets):
        # The shared fixture's 8:00-8:30 walk (Biscuit) overlaps the 8:15
        # feeding (Mochi) -- a conflict between two DIFFERENT pets.
        scheduler = Scheduler(owner_with_two_pets)
        conflicts = scheduler.find_conflicts()
        assert len(conflicts) == 1
        a, b = conflicts[0]
        assert {a.description, b.description} == {"Morning walk", "Feeding"}

    def test_tasks_on_different_dates_do_not_conflict(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        today_task = Task("Walk", time(8, 0), 30, scheduled_date=date(2026, 1, 1))
        tomorrow_task = Task("Walk", time(8, 0), 30, scheduled_date=date(2026, 1, 2))
        pet.add_task(today_task)
        pet.add_task(tomorrow_task)
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        assert scheduler.find_conflicts() == []


# ---- Phase 4/5: recurring tasks (creates a NEW task for the next occurrence) --------

class TestRecurringTasks:
    def test_completing_daily_task_creates_task_for_next_day(self, sample_pet):
        daily_task = Task(
            "Morning walk", time(8, 0), 30, Priority.HIGH, Frequency.DAILY,
            scheduled_date=date(2026, 3, 10),
        )
        sample_pet.add_task(daily_task)
        owner = Owner(name="Jordan")
        owner.add_pet(sample_pet)

        scheduler = Scheduler(owner)
        assert sample_pet.task_count() == 1

        new_task = scheduler.complete_task(daily_task)

        assert daily_task.completed is True
        assert new_task is not None
        assert new_task.completed is False
        assert new_task.scheduled_date == date(2026, 3, 11)  # today + 1 day
        assert new_task.scheduled_time == daily_task.scheduled_time
        assert sample_pet.task_count() == 2  # new task was attached to the pet

    def test_completing_weekly_task_creates_task_for_next_week(self, sample_pet):
        weekly_task = Task(
            "Grooming", time(10, 0), 60, Priority.MEDIUM, Frequency.WEEKLY,
            scheduled_date=date(2026, 3, 10),
        )
        sample_pet.add_task(weekly_task)
        owner = Owner(name="Jordan")
        owner.add_pet(sample_pet)

        scheduler = Scheduler(owner)
        new_task = scheduler.complete_task(weekly_task)

        assert new_task.scheduled_date == date(2026, 3, 17)  # today + 7 days

    def test_completing_once_task_creates_no_new_task(self, sample_pet):
        vet_visit = Task("Vet checkup", time(14, 0), 30, frequency=Frequency.ONCE)
        sample_pet.add_task(vet_visit)
        owner = Owner(name="Jordan")
        owner.add_pet(sample_pet)

        scheduler = Scheduler(owner)
        new_task = scheduler.complete_task(vet_visit)

        assert new_task is None
        assert vet_visit.completed is True
        assert sample_pet.task_count() == 1  # nothing new was added

    def test_next_occurrence_is_pure_and_does_not_mutate_original(self, sample_task):
        original_date = sample_task.scheduled_date
        next_task = sample_task.next_occurrence()
        assert sample_task.scheduled_date == original_date  # unchanged
        assert sample_task.completed is False  # next_occurrence() alone doesn't complete it
        assert next_task.scheduled_date == original_date + timedelta(days=1)

    def test_recurring_tasks_filter(self, owner_with_two_pets):
        scheduler = Scheduler(owner_with_two_pets)
        recurring = scheduler.recurring_tasks()
        assert len(recurring) == 4  # all sample tasks are DAILY


# ---- Challenge 1: next available slot -----------------------------------------------------

class TestFindNextAvailableSlot:
    def test_finds_gap_between_tasks(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        today = date(2026, 3, 10)
        # Back-to-back tasks from 6:00 (day_start) to 12:00 leave no gap
        # before lunch; the first real opening is right after lunch ends.
        pet.add_task(Task("Walk", time(6, 0), 360, scheduled_date=today))  # 6:00-12:00
        pet.add_task(Task("Lunch", time(12, 0), 30, scheduled_date=today))  # 12:00-12:30
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        slot = scheduler.find_next_available_slot(
            duration_minutes=60, for_date=today, day_start=time(6, 0), day_end=time(21, 0)
        )
        # first gap big enough for 60 min is right after lunch ends at 12:30
        assert slot == time(12, 30)

    def test_finds_earliest_slot_when_day_start_is_free(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        today = date(2026, 3, 10)
        pet.add_task(Task("Lunch", time(12, 0), 30, scheduled_date=today))
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        slot = scheduler.find_next_available_slot(
            duration_minutes=60, for_date=today, day_start=time(6, 0), day_end=time(21, 0)
        )
        # the gap from 6:00 to 12:00 is already big enough, so day_start wins
        assert slot == time(6, 0)

    def test_returns_none_when_fully_booked(self):
        owner = Owner(name="Sam")
        pet = Pet(name="Rex", species="Dog")
        today = date(2026, 3, 10)
        pet.add_task(Task("All day training", time(6, 0), 900, scheduled_date=today))
        owner.add_pet(pet)

        scheduler = Scheduler(owner)
        slot = scheduler.find_next_available_slot(
            duration_minutes=30, for_date=today, day_start=time(6, 0), day_end=time(21, 0)
        )
        assert slot is None

    def test_empty_day_returns_day_start(self):
        owner = Owner(name="Sam")
        owner.add_pet(Pet(name="Rex", species="Dog"))
        scheduler = Scheduler(owner)
        slot = scheduler.find_next_available_slot(
            duration_minutes=30, for_date=date(2026, 3, 10), day_start=time(6, 0)
        )
        assert slot == time(6, 0)


# ---- Challenge 2: JSON persistence -----------------------------------------------------

class TestJsonPersistence:
    def test_save_and_load_round_trip(self, owner_with_two_pets, tmp_path):
        filepath = os.path.join(tmp_path, "data.json")
        save_to_json(owner_with_two_pets, filepath)

        assert os.path.exists(filepath)
        with open(filepath) as f:
            raw = json.load(f)
        assert raw["name"] == "Jordan"

        loaded = load_from_json(filepath)
        assert loaded.name == "Jordan"
        assert len(loaded.pets) == 2
        assert loaded.find_pet("Mochi").species == "Cat"
        assert len(loaded.all_tasks()) == 4

    def test_loaded_tasks_preserve_enums_and_dates(self, sample_pet, tmp_path):
        task = Task(
            "Meds", time(9, 0), 5, Priority.HIGH, Frequency.WEEKLY,
            scheduled_date=date(2026, 3, 10),
        )
        sample_pet.add_task(task)
        owner = Owner(name="Jordan")
        owner.add_pet(sample_pet)

        filepath = os.path.join(tmp_path, "data.json")
        save_to_json(owner, filepath)
        loaded = load_from_json(filepath)

        loaded_task = loaded.pets[0].tasks[0]
        assert loaded_task.priority == Priority.HIGH
        assert loaded_task.frequency == Frequency.WEEKLY
        assert loaded_task.scheduled_date == date(2026, 3, 10)
        assert loaded_task.scheduled_time == time(9, 0)


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

    def test_build_daily_plan_only_includes_matching_date(self, sample_pet):
        owner = Owner(name="Jordan")
        owner.add_pet(sample_pet)
        today = date(2026, 3, 10)
        tomorrow = date(2026, 3, 11)
        sample_pet.add_task(Task("Today's walk", time(8, 0), 30, scheduled_date=today))
        sample_pet.add_task(Task("Tomorrow's walk", time(8, 0), 30, scheduled_date=tomorrow))

        scheduler = Scheduler(owner)
        result = scheduler.build_daily_plan(for_date=today)
        assert len(result["plan"]) == 1
        assert result["plan"][0].description == "Today's walk"
