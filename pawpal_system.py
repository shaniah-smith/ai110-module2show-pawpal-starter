"""
pawpal_system.py

The "logic layer" for PawPal+. Contains all backend classes:
    - Task: a single pet-care activity
    - Pet: a pet and the tasks associated with it
    - Owner: a person who manages one or more pets
    - Scheduler: builds and analyzes a daily plan across all of an owner's pets

This module has no UI code in it on purpose (see Phase 2 / CLI-first workflow).
`main.py` exercises it from the terminal, and `app.py` calls into it from Streamlit.

Stretch features implemented (see ai_interactions.md and README for details):
    - Challenge 1: Scheduler.find_next_available_slot() — a third algorithmic
      capability beyond sorting/filtering/conflicts.
    - Challenge 2: save_to_json() / load_from_json() — data persistence.
    - Challenge 3: Priority-based scheduling (Priority enum + sort_by_priority_then_time).
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import time, date, timedelta
from enum import Enum
from itertools import count
from typing import Optional


class Priority(Enum):
    """Relative importance of a task. Higher value = more important."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    def __str__(self) -> str:
        return self.name.capitalize()


class Frequency(Enum):
    """How often a task recurs."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


_task_id_counter = count(1)


@dataclass
class Task:
    """A single pet-care activity, e.g. a walk, a feeding, or a medication."""

    description: str
    scheduled_time: time
    duration_minutes: int = 15
    priority: Priority = Priority.MEDIUM
    frequency: Frequency = Frequency.ONCE
    scheduled_date: date = field(default_factory=date.today)
    completed: bool = False
    task_id: int = field(default_factory=lambda: next(_task_id_counter))

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not completed (e.g. resetting a recurring task)."""
        self.completed = False

    def next_occurrence(self) -> Optional["Task"]:
        """
        Return a new Task instance representing the next occurrence of a
        recurring task (DAILY -> +1 day, WEEKLY -> +7 days), or None if this
        task doesn't recur (ONCE). The new task starts incomplete.
        """
        if self.frequency == Frequency.DAILY:
            next_date = self.scheduled_date + timedelta(days=1)
        elif self.frequency == Frequency.WEEKLY:
            next_date = self.scheduled_date + timedelta(weeks=1)
        else:
            return None

        return Task(
            description=self.description,
            scheduled_time=self.scheduled_time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            scheduled_date=next_date,
            completed=False,
        )

    def end_time_minutes(self) -> int:
        """Return the minute-of-day this task ends, for conflict checks."""
        start = self.scheduled_time.hour * 60 + self.scheduled_time.minute
        return start + self.duration_minutes

    def start_time_minutes(self) -> int:
        """Return the minute-of-day this task starts, for conflict checks."""
        return self.scheduled_time.hour * 60 + self.scheduled_time.minute

    def overlaps_with(self, other: "Task") -> bool:
        """Return True if this task overlaps another task's time window on the same date."""
        if self.scheduled_date != other.scheduled_date:
            return False
        return (
            self.start_time_minutes() < other.end_time_minutes()
            and other.start_time_minutes() < self.end_time_minutes()
        )

    def to_dict(self) -> dict:
        """Convert this task to a JSON-serializable dict (Challenge 2: persistence)."""
        return {
            "description": self.description,
            "scheduled_time": self.scheduled_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.name,
            "frequency": self.frequency.name,
            "scheduled_date": self.scheduled_date.isoformat(),
            "completed": self.completed,
            "task_id": self.task_id,
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        """Rebuild a Task from a dict produced by to_dict() (Challenge 2: persistence)."""
        return Task(
            description=data["description"],
            scheduled_time=time.fromisoformat(data["scheduled_time"]),
            duration_minutes=data["duration_minutes"],
            priority=Priority[data["priority"]],
            frequency=Frequency[data["frequency"]],
            scheduled_date=date.fromisoformat(data["scheduled_date"]),
            completed=data["completed"],
            task_id=data["task_id"],
        )

    def __str__(self) -> str:
        status = "[x]" if self.completed else "[ ]"
        return (
            f"{status} {self.scheduled_time.strftime('%I:%M %p')} - "
            f"{self.description} ({self.duration_minutes} min) "
            f"[{self.priority}]"
        )


@dataclass
class Pet:
    """A pet belonging to an Owner, with its own list of care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a new task to this pet's task list."""
        self.tasks.append(task)

    def task_count(self) -> int:
        """Return how many tasks this pet currently has."""
        return len(self.tasks)

    def incomplete_tasks(self) -> list[Task]:
        """Return only the tasks that have not been completed yet."""
        return [t for t in self.tasks if not t.completed]

    def to_dict(self) -> dict:
        """Convert this pet (and its tasks) to a JSON-serializable dict."""
        return {
            "name": self.name,
            "species": self.species,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @staticmethod
    def from_dict(data: dict) -> "Pet":
        """Rebuild a Pet (and its tasks) from a dict produced by to_dict()."""
        pet = Pet(name=data["name"], species=data["species"])
        pet.tasks = [Task.from_dict(t) for t in data["tasks"]]
        return pet

    def __str__(self) -> str:
        return f"{self.name} ({self.species})"


@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across every pet this owner has."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def find_pet(self, name: str) -> Optional[Pet]:
        """Look up one of this owner's pets by name."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def find_pet_for_task(self, task: Task) -> Optional[Pet]:
        """Find which of this owner's pets a given task belongs to."""
        for pet in self.pets:
            if task in pet.tasks:
                return pet
        return None

    def to_dict(self) -> dict:
        """Convert this owner (and all pets/tasks) to a JSON-serializable dict."""
        return {"name": self.name, "pets": [p.to_dict() for p in self.pets]}

    @staticmethod
    def from_dict(data: dict) -> "Owner":
        """Rebuild an Owner (and all pets/tasks) from a dict produced by to_dict()."""
        owner = Owner(name=data["name"])
        owner.pets = [Pet.from_dict(p) for p in data["pets"]]
        return owner


# ---------------------------------------------------------------------------
# Persistence (Challenge 2: Data Persistence)
# ---------------------------------------------------------------------------

def save_to_json(owner: Owner, filepath: str = "data.json") -> None:
    """Save an Owner (and all of their pets/tasks) to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(owner.to_dict(), f, indent=2)


def load_from_json(filepath: str = "data.json") -> Owner:
    """Load an Owner (and all of their pets/tasks) from a JSON file."""
    with open(filepath, "r") as f:
        data = json.load(f)
    return Owner.from_dict(data)


class Scheduler:
    """
    The "brain" of PawPal+. Retrieves tasks from an Owner's pets and applies
    algorithmic logic: sorting, filtering by available time/pet/status,
    conflict detection, recurring-task handling, and next-available-slot
    lookup.
    """

    def __init__(self, owner: Owner):
        self.owner = owner

    # ---- retrieval -----------------------------------------------------

    def get_all_tasks(self) -> list[Task]:
        """Ask the Owner for every task across all of their pets."""
        return self.owner.all_tasks()

    # ---- sorting -----------------------------------------------------

    def sort_by_priority_then_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """
        Sort tasks by priority (high first), then by scheduled time within
        the same priority. This is the default ordering for "today's plan".
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(
            tasks,
            key=lambda t: (-t.priority.value, t.start_time_minutes()),
        )

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Sort tasks purely chronologically (by time-of-day), ignoring priority."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: t.start_time_minutes())

    # ---- filtering -----------------------------------------------------

    def filter_within_time_budget(
        self, tasks: list[Task], minutes_available: int
    ) -> tuple[list[Task], list[Task]]:
        """
        Given a priority-ordered list of tasks and a total time budget,
        greedily select tasks that fit, highest priority first.

        Returns a tuple of (selected_tasks, skipped_tasks).
        """
        selected: list[Task] = []
        skipped: list[Task] = []
        remaining = minutes_available

        for task in tasks:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes
            else:
                skipped.append(task)

        return selected, skipped

    def filter_incomplete(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return only tasks that have not been marked complete."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if not t.completed]

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return only the tasks belonging to the named pet."""
        pet = self.owner.find_pet(pet_name)
        return list(pet.tasks) if pet else []

    def filter_by_date(self, for_date: date, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return only tasks scheduled on the given date."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.scheduled_date == for_date]

    # ---- conflict detection -----------------------------------------------------

    def find_conflicts(self, tasks: Optional[list[Task]] = None) -> list[tuple[Task, Task]]:
        """
        Detect overlapping time slots among tasks on the same date (e.g. two
        tasks for different pets scheduled at the same time). Returns a
        lightweight list of conflicting task pairs rather than raising an
        error, so the caller can display a warning instead of crashing.
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        ordered = self.sort_by_time(tasks)
        conflicts: list[tuple[Task, Task]] = []

        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                if ordered[i].overlaps_with(ordered[j]):
                    conflicts.append((ordered[i], ordered[j]))

        return conflicts

    # ---- recurring tasks -----------------------------------------------------

    def complete_task(self, task: Task) -> Optional[Task]:
        """
        Mark a task complete. If it recurs (DAILY/WEEKLY), automatically
        create and attach a new Task instance for the next occurrence
        (today + 1 day, or + 1 week) to the same pet. Returns the newly
        created task, or None if the task doesn't recur.
        """
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet = self.owner.find_pet_for_task(task)
            if pet is not None:
                pet.add_task(next_task)
        return next_task

    def recurring_tasks(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return only tasks that recur (DAILY or WEEKLY), for review/reporting."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.frequency != Frequency.ONCE]

    # ---- Challenge 1: next available slot -----------------------------------------------------

    def find_next_available_slot(
        self,
        duration_minutes: int,
        for_date: Optional[date] = None,
        day_start: time = time(6, 0),
        day_end: time = time(21, 0),
    ) -> Optional[time]:
        """
        Stretch feature (Challenge 1): find the earliest open time slot on a
        given date (default: today) that can fit a task of the requested
        duration, considering all of the owner's existing tasks that day.
        Returns None if no slot of that length is available before day_end.
        """
        for_date = for_date or date.today()
        day_tasks = sorted(
            self.filter_by_date(for_date),
            key=lambda t: t.start_time_minutes(),
        )

        day_start_min = day_start.hour * 60 + day_start.minute
        day_end_min = day_end.hour * 60 + day_end.minute
        cursor = day_start_min

        for task in day_tasks:
            gap = task.start_time_minutes() - cursor
            if gap >= duration_minutes:
                return time(cursor // 60, cursor % 60)
            cursor = max(cursor, task.end_time_minutes())

        if day_end_min - cursor >= duration_minutes:
            return time(cursor // 60, cursor % 60)

        return None

    # ---- the full daily plan -----------------------------------------------------

    def build_daily_plan(
        self,
        minutes_available: Optional[int] = None,
        for_date: Optional[date] = None,
    ) -> dict:
        """
        Build the plan for a given date (default: today): incomplete tasks
        scheduled on that date, sorted by priority then time, optionally
        trimmed to a time budget, with any scheduling conflicts flagged
        separately so the owner can resolve them.

        Returns a dict with keys: "plan", "skipped", "conflicts".
        """
        for_date = for_date or date.today()
        todays_tasks = self.filter_by_date(for_date)
        incomplete = self.filter_incomplete(todays_tasks)
        ordered = self.sort_by_priority_then_time(incomplete)

        if minutes_available is not None:
            plan, skipped = self.filter_within_time_budget(ordered, minutes_available)
        else:
            plan, skipped = ordered, []

        conflicts = self.find_conflicts(plan)

        return {
            "plan": self.sort_by_time(plan),
            "skipped": skipped,
            "conflicts": conflicts,
        }
