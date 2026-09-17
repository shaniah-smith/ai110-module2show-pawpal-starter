# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

The system is designed first (UML), then implemented in Python (`pawpal_system.py`), verified from the
terminal (`main.py`, `tests/`), and finally connected to a Streamlit UI (`app.py`).

## What this app does

- Lets a user enter owner + pet info and add multiple pets
- Lets a user add tasks per pet with a time, duration, priority, and frequency (once/daily/weekly)
- Generates a daily schedule that:
  - Sorts tasks by priority, then by time
  - Optionally fits tasks into a time budget (greedy selection, highest priority first)
  - Detects overlapping/conflicting time slots across a pet's (or all pets') tasks
  - Tracks recurring (daily/weekly) tasks separately from one-off tasks
- Displays the plan, any skipped tasks, and any conflicts, with reasoning visible in the UI
- Includes a pytest suite covering the scheduling behaviors above

## System Design

### Classes

| Class | Responsibility |
|---|---|
| `Task` | Represents a single care activity: description, scheduled time, duration, priority, recurrence, and completion status. Knows how to compute its own start/end time and whether it overlaps another task. |
| `Pet` | Holds a pet's identity (name, species) and its list of `Task`s. |
| `Owner` | Holds one or more `Pet`s and can retrieve every task across all of them. |
| `Scheduler` | The "brain." Takes an `Owner` and applies algorithmic logic on top of the raw task data: sorting, time-budget filtering, conflict detection, and recurring-task resets. Produces the final daily plan. |

### UML Diagram

See [`diagrams/uml.mmd`](diagrams/uml.mmd) (Mermaid class diagram — paste into
[Mermaid Live Editor](https://mermaid.live/) or preview it in VS Code with a Mermaid extension).

`Owner` has many `Pet`s, each `Pet` has many `Task`s, and `Scheduler` reads from (but does not own) an
`Owner` to build the plan — keeping the scheduling *logic* separate from the *data model*.

## Getting started

### Setup

```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the CLI demo

```
python main.py
```

### Run the Streamlit app

```
streamlit run app.py
```

## 🖥️ Sample Output

Output from `python main.py`, using a sample owner ("Jordan") with two pets (Biscuit the dog, Mochi the
cat) and six tasks across them:

```
📋 Today's Schedule for Jordan's pets
==================================================
  [ ] 08:00 AM - Morning walk (30 min) [High]  — Biscuit
  [ ] 08:15 AM - Feeding (10 min) [Medium]  — Mochi
  [ ] 08:30 AM - Breakfast (10 min) [High]  — Biscuit
  [ ] 09:00 AM - Heartworm medication (5 min) [High]  — Biscuit
  [ ] 09:30 AM - Litter box cleaning (10 min) [Low]  — Mochi
  [ ] 02:00 PM - Vet appointment check-in call (15 min) [Medium]  — Mochi

⚠️  Scheduling conflicts detected:
  Morning walk overlaps with Feeding
==================================================
```

Note the conflict warning: Biscuit's 30-minute walk (8:00–8:30 AM) overlaps Mochi's 8:15 AM feeding —
this is exactly the kind of scheduling collision the `Scheduler.find_conflicts()` algorithm is designed
to catch and surface to the owner.

## 🧪 Testing PawPal+

```
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/claude/pawpal-plus
collected 21 items

tests/test_pawpal.py::TestTaskCompletion::test_mark_complete_changes_status PASSED [  4%]
tests/test_pawpal.py::TestTaskCompletion::test_mark_incomplete_resets_status PASSED [  9%]
tests/test_pawpal.py::TestTaskAddition::test_add_task_increases_count PASSED [ 14%]
tests/test_pawpal.py::TestTaskAddition::test_adding_multiple_tasks PASSED [ 19%]
tests/test_pawpal.py::TestOwner::test_all_tasks_collects_across_pets PASSED [ 23%]
tests/test_pawpal.py::TestOwner::test_find_pet_by_name PASSED            [ 28%]
tests/test_pawpal.py::TestOwner::test_find_pet_missing_returns_none PASSED [ 33%]
tests/test_pawpal.py::TestSorting::test_sort_by_priority_then_time PASSED [ 38%]
tests/test_pawpal.py::TestSorting::test_sort_by_time PASSED              [ 42%]
tests/test_pawpal.py::TestTimeBudgetFiltering::test_filter_within_time_budget_selects_highest_priority_first PASSED [ 47%]
tests/test_pawpal.py::TestTimeBudgetFiltering::test_filter_with_zero_budget_skips_everything PASSED [ 52%]
tests/test_pawpal.py::TestConflictDetection::test_detects_overlapping_tasks PASSED [ 57%]
tests/test_pawpal.py::TestConflictDetection::test_no_conflicts_for_sequential_tasks PASSED [ 61%]
tests/test_pawpal.py::TestConflictDetection::test_owner_with_two_pets_fixture_has_a_detectable_conflict PASSED [ 66%]
tests/test_pawpal.py::TestConflictDetection::test_back_to_back_tasks_do_not_conflict PASSED [ 71%]
tests/test_pawpal.py::TestRecurringTasks::test_reset_recurring_tasks_only_resets_daily PASSED [ 76%]
tests/test_pawpal.py::TestRecurringTasks::test_once_tasks_are_not_reset PASSED [ 80%]
tests/test_pawpal.py::TestRecurringTasks::test_recurring_tasks_filter PASSED [ 85%]
tests/test_pawpal.py::TestBuildDailyPlan::test_build_daily_plan_without_budget_includes_all_incomplete PASSED [ 90%]
tests/test_pawpal.py::TestBuildDailyPlan::test_completed_tasks_excluded_from_plan PASSED [ 95%]
tests/test_pawpal.py::TestBuildDailyPlan::test_build_daily_plan_respects_time_budget PASSED [100%]

============================== 21 passed in 0.02s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---|---|---|
| Task sorting | `Scheduler.sort_by_priority_then_time()`, `Scheduler.sort_by_time()` | Primary plan ordering is by priority (High → Low), then by time within the same priority. A pure chronological sort is also available. |
| Filtering | `Scheduler.filter_within_time_budget()`, `Scheduler.filter_incomplete()` | Greedily selects tasks that fit inside an owner's available minutes, highest priority first; separately filters out already-completed tasks. |
| Conflict handling | `Task.overlaps_with()`, `Scheduler.find_conflicts()` | Compares every pair of tasks' start/end minute-of-day windows and reports overlapping pairs (e.g., two pets' tasks scheduled at the same time) rather than silently allowing double-booking. |
| Recurring tasks | `Task.frequency` (`ONCE` / `DAILY` / `WEEKLY`), `Scheduler.reset_recurring_tasks()`, `Scheduler.recurring_tasks()` | Daily tasks are automatically reset to incomplete so they reappear on the next day's plan; one-off tasks are not. |

## 📸 Demo Walkthrough

1. Enter the owner's name (e.g., "Jordan") at the top of the app.
2. Add a pet by entering its name and species, then click **Add pet**. Repeat for a second pet.
3. Select a pet from the dropdown, fill in a task's title, time, duration, priority, and frequency, then
   click **Add task**. Repeat to add a few tasks across both pets, including two that overlap in time.
4. (Optional) Enter a time budget in minutes if you want the scheduler to trim the plan to fit.
5. Click **Generate schedule** to see the prioritized plan, any skipped tasks (if a time budget was set),
   and any scheduling conflicts PawPal+ detected between overlapping tasks.

**Screenshot or video** *(optional)*:
