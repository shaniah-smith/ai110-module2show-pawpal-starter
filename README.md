# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

The system was designed first (UML), then implemented in Python (`pawpal_system.py`), verified from the
terminal (`main.py`, `tests/`), and finally connected to a Streamlit UI (`app.py`).

## Features

- **Owner / Pet / Task modeling:** represent an owner with multiple pets, each with its own list of
  care tasks (description, time, duration, priority, recurrence).
- **Priority-based scheduling:** `Scheduler.sort_by_priority_then_time()` sorts tasks High to Low, then
  chronologically within a priority tier, so urgent care never gets buried.
- **Time-budget filtering:** `Scheduler.filter_within_time_budget()` greedily fits as many
  high-priority tasks as possible into however many minutes the owner has today.
- **Filter by pet or completion status:** `Scheduler.filter_by_pet()` and `Scheduler.filter_incomplete()`.
- **Conflict detection:** `Scheduler.find_conflicts()` flags any two tasks (same pet or different pets)
  whose time windows overlap, including exact-duplicate times, without crashing the app.
- **Recurring tasks that self-schedule:** `Scheduler.complete_task()` marks a task done and, if it's
  DAILY or WEEKLY, automatically creates the next occurrence (`today + 1 day` / `+ 1 week`) for that pet.
- **Next-available-slot finder** *(stretch, Challenge 1)*: `Scheduler.find_next_available_slot()` scans
  a day's existing tasks and returns the earliest open window long enough for a new task.
- **JSON persistence** *(stretch, Challenge 2)*: `save_to_json()` / `load_from_json()` let an owner's
  pets and tasks survive between runs.
- **Formatted CLI output** *(stretch, Challenge 4)*: `main.py` renders the schedule as a table
  (via `tabulate`) with priority emoji, instead of a raw object dump.

## System Design

### Classes

| Class | Responsibility |
|---|---|
| `Task` | Represents a single care activity: description, scheduled time + date, duration, priority, recurrence, and completion status. Knows how to compute its own start/end time, detect overlap with another task, generate its own next occurrence, and serialize to/from a dict. |
| `Pet` | Holds a pet's identity (name, species) and its list of `Task`s. |
| `Owner` | Holds one or more `Pet`s, can retrieve every task across all of them, and can look up which pet a given task belongs to. |
| `Scheduler` | The "brain." Takes an `Owner` and applies algorithmic logic on top of the raw task data: sorting, filtering (time budget / pet / status / date), conflict detection, recurring-task completion, and next-available-slot lookup. Produces the final daily plan. |

### UML Diagram

- [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd): the initial Phase 1 draft (four classes, minimal
  attributes/methods), sketched before any implementation.
- [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) / [`diagrams/uml.mmd`](diagrams/uml.mmd): the
  final diagram, updated in Phase 6 to match `pawpal_system.py` exactly (enums, `scheduled_date`,
  `next_occurrence()`, persistence methods, and the full `Scheduler` algorithmic layer).

Paste any of these into [Mermaid Live Editor](https://mermaid.live/) or preview them in VS Code with a
Mermaid extension. `Owner` has many `Pet`s, each `Pet` has many `Task`s, and `Scheduler` reads from (but
does not own) an `Owner`, keeping scheduling *logic* separate from the *data model*.

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
cat). Tasks are added **out of order** on purpose to prove the sorting logic actually reorders them:

```

📋 Today's Schedule for Jordan's pets
============================================================
Time      Task                           Pet      Duration    Priority
--------  -----------------------------  -------  ----------  ----------
08:00 AM  Morning walk                   Biscuit  30 min      🔴 High
08:00 AM  Feeding                        Mochi    10 min      🟡 Medium
08:30 AM  Breakfast                      Biscuit  10 min      🔴 High
09:00 AM  Heartworm medication           Biscuit  5 min       🔴 High
09:30 AM  Litter box cleaning            Mochi    10 min      🟢 Low
02:00 PM  Vet appointment check-in call  Mochi    15 min      🟡 Medium

⚠️  Scheduling conflicts detected:
  'Morning walk' overlaps with 'Feeding' at 08:00 AM
============================================================

🔁 Recurring task demo
============================================================
Before: Biscuit has 3 tasks
Marked 'Morning walk' complete (frequency: daily)
-> Auto-created next occurrence for 2026-10-02 at 08:00 AM
After:  Biscuit has 4 tasks
============================================================

🔎 Sorting & filtering demo
============================================================

Today's tasks sorted by priority, then time:
  2026-10-01  08:00 AM  Morning walk                   Biscuit  High    done
  2026-10-01  08:30 AM  Breakfast                      Biscuit  High    pending
  2026-10-01  09:00 AM  Heartworm medication           Biscuit  High    pending
  2026-10-01  08:00 AM  Feeding                        Mochi    Medium  pending
  2026-10-01  02:00 PM  Vet appointment check-in call  Mochi    Medium  pending
  2026-10-01  09:30 AM  Litter box cleaning            Mochi    Low     pending

Filter: Mochi's tasks only:
  2026-10-01  08:00 AM  Feeding                        Mochi    Medium  pending
  2026-10-01  09:30 AM  Litter box cleaning            Mochi    Low     pending
  2026-10-01  02:00 PM  Vet appointment check-in call  Mochi    Medium  pending

Filter: incomplete tasks only (today's completed walk is gone; tomorrow's remains):
  2026-10-01  08:00 AM  Feeding                        Mochi    Medium  pending
  2026-10-01  08:30 AM  Breakfast                      Biscuit  High    pending
  2026-10-01  09:00 AM  Heartworm medication           Biscuit  High    pending
  2026-10-01  09:30 AM  Litter box cleaning            Mochi    Low     pending
  2026-10-01  02:00 PM  Vet appointment check-in call  Mochi    Medium  pending
  2026-10-02  08:00 AM  Morning walk                   Biscuit  High    pending
============================================================

🕒 Next available 20-minute slot (Challenge 1)
============================================================
Next available slot today: 06:00 AM
============================================================

💾 Persistence demo (Challenge 2)
============================================================
Saved owner + pets + tasks to data.json
Reloaded owner 'Jordan' with 2 pets and 7 total tasks
============================================================
```

Note the conflict warning: Biscuit's 30-minute walk (8:00 to 8:30 AM) overlaps Mochi's 8:00 AM feeding,
exactly the kind of cross-pet scheduling collision `Scheduler.find_conflicts()` is designed to catch.
The recurring-task demo then marks that same walk complete and shows `Scheduler.complete_task()`
auto-creating tomorrow's walk for Biscuit, rather than just resetting a flag.

## 🧪 Testing PawPal+

```
# Run the full test suite:
python -m pytest

# Run with coverage:
python -m pytest --cov
```

The suite (36 tests) covers:
- **Required checks:** `mark_complete()` changes status; adding a task increases a pet's task count.
- **Sorting correctness:** tasks added out of order come back in chronological order, and priority sort
  puts High before Medium/Low.
- **Filtering:** time-budget filtering, filtering by pet, filtering by completion status.
- **Conflict detection:** overlapping tasks, exact-duplicate times, back-to-back tasks (no false
  positive), cross-pet conflicts, and tasks on different dates (no false positive).
- **Recurrence:** completing a DAILY task creates a new task dated `+1 day`; completing a WEEKLY task
  creates one dated `+1 week`; completing a ONCE task creates nothing.
- **Stretch features:** next-available-slot lookup (Challenge 1) and JSON save/load round-tripping,
  including that enums and dates survive serialization (Challenge 2).

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/shaniahsmith/Desktop/ai110-module2show-pawpal-starter/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/shaniahsmith/Desktop/ai110-module2show-pawpal-starter
plugins: cov-7.1.0, anyio-4.15.1
collecting ... collected 36 items

tests/test_pawpal.py::TestTaskCompletion::test_mark_complete_changes_status PASSED [  2%]
tests/test_pawpal.py::TestTaskCompletion::test_mark_incomplete_resets_status PASSED [  5%]
tests/test_pawpal.py::TestTaskAddition::test_add_task_increases_count PASSED [  8%]
tests/test_pawpal.py::TestTaskAddition::test_adding_multiple_tasks PASSED [ 11%]
tests/test_pawpal.py::TestOwner::test_all_tasks_collects_across_pets PASSED [ 13%]
tests/test_pawpal.py::TestOwner::test_find_pet_by_name PASSED            [ 16%]
tests/test_pawpal.py::TestOwner::test_find_pet_missing_returns_none PASSED [ 19%]
tests/test_pawpal.py::TestOwner::test_find_pet_for_task PASSED           [ 22%]
tests/test_pawpal.py::TestSorting::test_sort_by_priority_then_time PASSED [ 25%]
tests/test_pawpal.py::TestSorting::test_sort_by_time_is_chronological PASSED [ 27%]
tests/test_pawpal.py::TestTimeBudgetFiltering::test_filter_within_time_budget_selects_highest_priority_first PASSED [ 30%]
tests/test_pawpal.py::TestTimeBudgetFiltering::test_filter_with_zero_budget_skips_everything PASSED [ 33%]
tests/test_pawpal.py::TestFilterByPetAndStatus::test_filter_by_pet_name PASSED [ 36%]
tests/test_pawpal.py::TestFilterByPetAndStatus::test_filter_by_pet_unknown_returns_empty PASSED [ 38%]
tests/test_pawpal.py::TestFilterByPetAndStatus::test_filter_incomplete_excludes_completed PASSED [ 41%]
tests/test_pawpal.py::TestConflictDetection::test_detects_overlapping_tasks PASSED [ 44%]
tests/test_pawpal.py::TestConflictDetection::test_detects_exact_duplicate_times PASSED [ 47%]
tests/test_pawpal.py::TestConflictDetection::test_no_conflicts_for_sequential_tasks PASSED [ 50%]
tests/test_pawpal.py::TestConflictDetection::test_back_to_back_tasks_do_not_conflict PASSED [ 52%]
tests/test_pawpal.py::TestConflictDetection::test_conflict_across_different_pets PASSED [ 55%]
tests/test_pawpal.py::TestConflictDetection::test_tasks_on_different_dates_do_not_conflict PASSED [ 58%]
tests/test_pawpal.py::TestRecurringTasks::test_completing_daily_task_creates_task_for_next_day PASSED [ 61%]
tests/test_pawpal.py::TestRecurringTasks::test_completing_weekly_task_creates_task_for_next_week PASSED [ 63%]
tests/test_pawpal.py::TestRecurringTasks::test_completing_once_task_creates_no_new_task PASSED [ 66%]
tests/test_pawpal.py::TestRecurringTasks::test_next_occurrence_is_pure_and_does_not_mutate_original PASSED [ 69%]
tests/test_pawpal.py::TestRecurringTasks::test_recurring_tasks_filter PASSED [ 72%]
tests/test_pawpal.py::TestFindNextAvailableSlot::test_finds_gap_between_tasks PASSED [ 75%]
tests/test_pawpal.py::TestFindNextAvailableSlot::test_finds_earliest_slot_when_day_start_is_free PASSED [ 77%]
tests/test_pawpal.py::TestFindNextAvailableSlot::test_returns_none_when_fully_booked PASSED [ 80%]
tests/test_pawpal.py::TestFindNextAvailableSlot::test_empty_day_returns_day_start PASSED [ 83%]
tests/test_pawpal.py::TestJsonPersistence::test_save_and_load_round_trip PASSED [ 86%]
tests/test_pawpal.py::TestJsonPersistence::test_loaded_tasks_preserve_enums_and_dates PASSED [ 88%]
tests/test_pawpal.py::TestBuildDailyPlan::test_build_daily_plan_without_budget_includes_all_incomplete PASSED [ 91%]
tests/test_pawpal.py::TestBuildDailyPlan::test_completed_tasks_excluded_from_plan PASSED [ 94%]
tests/test_pawpal.py::TestBuildDailyPlan::test_build_daily_plan_respects_time_budget PASSED [ 97%]
tests/test_pawpal.py::TestBuildDailyPlan::test_build_daily_plan_only_includes_matching_date PASSED [100%]

============================== 36 passed in 0.03s ==============================
```

**Confidence Level: ⭐⭐⭐⭐ (4/5)**

36 tests pass across every core and stretch behavior, including several edge cases (zero-minute budget,
back-to-back tasks, different dates, fully-booked days). I'd call it 4 rather than 5 stars because the
edge cases I'd still want to add (see reflection.md section 4b) involve less common scenarios (tasks
spanning midnight, three-way conflicts) that the current suite doesn't cover yet.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---|---|---|
| Task sorting | `Scheduler.sort_by_priority_then_time()`, `Scheduler.sort_by_time()` | Primary plan ordering is by priority (High to Low), then by time within the same priority. A pure chronological sort is also available. |
| Filtering | `Scheduler.filter_within_time_budget()`, `Scheduler.filter_incomplete()`, `Scheduler.filter_by_pet()`, `Scheduler.filter_by_date()` | Greedily selects tasks that fit inside an owner's available minutes (highest priority first); filters by completion status, by a specific pet's name, or by date. |
| Conflict handling | `Task.overlaps_with()`, `Scheduler.find_conflicts()` | Compares every pair of same-date tasks' start/end minute-of-day windows (not just exact-time matches) and returns a lightweight list of conflicting pairs, whether from the same pet or different pets, instead of crashing. |
| Recurring tasks | `Task.frequency` (`ONCE`/`DAILY`/`WEEKLY`), `Task.next_occurrence()`, `Scheduler.complete_task()` | Completing a DAILY or WEEKLY task automatically creates and attaches a **new** `Task` for the next day (or next week) to the same pet, using `timedelta`. `ONCE` tasks generate nothing further. |
| Next available slot *(stretch)* | `Scheduler.find_next_available_slot()` | Scans a day's tasks in order and returns the earliest gap (within a configurable day window) long enough for a new task of a given duration. |

## 💾 Data Persistence (Challenge 2)

`Owner`, `Pet`, and `Task` each implement `to_dict()` / `from_dict()`, and `pawpal_system.py` exposes:

```python
save_to_json(owner, "data.json")
owner = load_from_json("data.json")
```

`Task.to_dict()` converts the `Priority`/`Frequency` enums to their names and the `time`/`date` fields to
ISO strings so the result is plain-JSON-serializable; `from_dict()` reverses each of those conversions.
`main.py`'s persistence demo saves the sample owner to `data.json`, then reloads it into a fresh `Owner`
object and confirms the pet/task counts match: a full round trip. Files modified: `pawpal_system.py`
(new functions/methods), `main.py` (demo call), `tests/test_pawpal.py` (round-trip tests).

## 📸 Demo Walkthrough

**Main UI features:** enter an owner name; add one or more pets (name + species); add tasks to a pet
(title, time, duration, priority, frequency); get a slot suggestion for a new task; filter the task list
by pet; mark a task complete (auto-creating its next occurrence if it recurs); generate a prioritized
daily schedule with conflict warnings.

**Example workflow:**
1. Enter the owner's name (e.g., "Jordan") at the top of the app.
2. Add a pet by entering its name and species, then click **Add pet**. Repeat for a second pet.
3. Select a pet from the dropdown, fill in a task's title, time, duration, priority, and frequency, then
   click **Add task**. Add a few tasks across both pets, including two that overlap in time.
4. Use **Find next available slot** to see where a new task would fit without a conflict.
5. Filter the task table by pet, then select a DAILY task and click **Mark complete**. Notice the
   success message confirming a new task was created for tomorrow.
6. (Optional) Enter a time budget in minutes so the scheduler trims the plan to fit.
7. Click **Generate schedule** to see the prioritized plan, any skipped tasks, and any scheduling
   conflicts PawPal+ detected between overlapping tasks.

**Key Scheduler behaviors shown:** priority-then-time sorting, time-budget filtering, cross-pet conflict
warnings, and automatic recurrence (a completed daily task spawning tomorrow's task).

**Sample CLI output** (from `python main.py`): see the [🖥️ Sample Output](#️-sample-output) section
above for the full fenced code block.

