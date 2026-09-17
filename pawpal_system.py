"""
pawpal_system.py

The "logic layer" for PawPal+. Contains all backend classes:
    - Task: a single pet-care activity
    - Pet: a pet and the tasks associated with it
    - Owner: a person who manages one or more pets
    - Scheduler: builds and analyzes a daily plan across all of an owner's pets

This module has no UI code in it on purpose (see Phase 2 / CLI-first workflow).
`main.py` exercises it from the terminal, and `app.py` calls into it from Streamlit.
"""

from dataclasses import dataclass, field
from datetime import time
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
    completed: bool = False
    task_id: int = field(default_factory=lambda: next(_task_id_counter))

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not completed (e.g. resetting a recurring task)."""
        self.completed = False

    def end_time_minutes(self) -> int:
        """Return the minute-of-day this task ends, for conflict checks."""
        start = self.scheduled_time.hour * 60 + self.scheduled_time.minute
        return start + self.duration_minutes

    def start_time_minutes(self) -> int:
        """Return the minute-of-day this task starts, for conflict checks."""
        return self.scheduled_time.hour * 60 + self.scheduled_time.minute

    def overlaps_with(self, other: "Task") -> bool:
        """Return True if this task's time window overlaps another task's window."""
        return (
            self.start_time_minutes() < other.end_time_minutes()
            and other.start_time_minutes() < self.end_time_minutes()
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


class Scheduler:
    """
    The "brain" of PawPal+. Retrieves tasks from an Owner's pets and applies
    algorithmic logic: sorting, filtering by available time, conflict
    detection, and recurring-task handling.
    """

    def __init__(self, owner: Owner):
        self.owner = owner

    # ---- retrieval -------------------------------------------------

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
        """Sort tasks purely chronologically, ignoring priority."""
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

    # ---- conflict detection -----------------------------------------------------

    def find_conflicts(self, tasks: Optional[list[Task]] = None) -> list[tuple[Task, Task]]:
        """
        Detect overlapping time slots among tasks (e.g. two tasks for
        different pets scheduled at the same time). Returns a list of
        conflicting task pairs.
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

    def reset_recurring_tasks(self, tasks: Optional[list[Task]] = None) -> int:
        """
        Reset the `completed` flag on any DAILY task so it reappears on the
        next day's schedule. WEEKLY and ONCE tasks are left untouched.
        Returns how many tasks were reset.
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        reset_count = 0
        for task in tasks:
            if task.frequency == Frequency.DAILY and task.completed:
                task.mark_incomplete()
                reset_count += 1
        return reset_count

    def recurring_tasks(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return only tasks that recur (DAILY or WEEKLY), for review/reporting."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.frequency != Frequency.ONCE]

    # ---- the full daily plan -----------------------------------------------------

    def build_daily_plan(
        self, minutes_available: Optional[int] = None
    ) -> dict:
        """
        Build today's plan: incomplete tasks, sorted by priority then time,
        optionally trimmed to a time budget, with any scheduling conflicts
        flagged separately so the owner can resolve them.

        Returns a dict with keys: "plan", "skipped", "conflicts".
        """
        incomplete = self.filter_incomplete()
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
