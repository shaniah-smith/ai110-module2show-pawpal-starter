# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design had four classes: `Owner`, `Pet`, `Task`, and `Scheduler`. `Owner` holds a list of
`Pet`s and is responsible for aggregating data across them (e.g., returning every task an owner is
responsible for). `Pet` holds its own list of `Task`s and basic identity info (name, species). `Task` is
a plain data holder for one care activity (description, time, duration, priority, frequency, completion
status) plus a couple of small helper methods (`mark_complete`, `overlaps_with`). `Scheduler` was the odd
one out on purpose: instead of putting scheduling logic *inside* `Owner` or `Pet`, I gave it its own class
that takes an `Owner` and reads from it, so all of the "smart" behavior (sorting, filtering, conflict
detection, recurring resets) lives in one place separate from the plain data model.

**b. Design changes**

The biggest change was splitting "priority" and "frequency" out into their own `Enum` classes (`Priority`,
`Frequency`) instead of using plain strings on `Task`. Early on I was comparing strings like
`"high" == "High"` and it was fragile: a typo anywhere would silently break sorting. Enums caught that at
the class definition level instead, and let me sort by `Priority.HIGH.value` instead of writing a manual
string-to-number lookup every time I needed to compare priorities.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: task **priority** (High/Medium/Low), a **time budget** in
minutes (optional: an owner can say "I only have 40 minutes today"), and **time-of-day conflicts**
between tasks. Priority mattered most because in a real pet-care scenario, a missed medication is a much
bigger problem than a missed round of enrichment play, so the plan should always surface high-priority
items first regardless of what order they were entered in.

**b. Tradeoffs**

`filter_within_time_budget()` uses a greedy algorithm: it walks the priority-sorted task list in order
and takes a task if it fits in the remaining budget, otherwise it skips it and moves on. It does not try
to find the *optimal* combination of tasks that maximizes total priority within the budget (that would be
closer to a knapsack problem). This is a reasonable tradeoff here because the greedy approach is simple,
fast, and predictable: an owner glancing at a skipped Low-priority task understands immediately why it
was cut, whereas an optimal-but-opaque solver might skip a High-priority task in favor of two Low-priority
ones that "pack" better, which would feel wrong to a pet owner even if the math checks out.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI during the design phase to sanity-check my initial four-class breakdown before writing any code,
and to generate the Mermaid.js class diagram from my brainstormed attributes/methods so I didn't have to
hand-write Mermaid syntax. During implementation, I used AI to scaffold the class skeletons from the UML
and to draft the pytest test cases once the core logic existed. The most useful prompts were narrow and
gave the AI the actual code as context, e.g., "based on my skeletons in pawpal_system.py, how should the
Scheduler retrieve all tasks from the Owner's pets?", rather than broad, open-ended prompts, which tended
to produce generic advice that didn't fit the classes I'd already sketched out.

**b. Judgment and verification**

One place I did not accept the AI's suggestion as-is was conflict detection. Its first draft only checked
whether two tasks had the exact same `scheduled_time`, which misses the much more common case of a
30-minute walk that *overlaps* a task starting partway through it. I verified this by writing a test case
first (two tasks with a 15-minute overlap but different start times) and running it against the
suggested implementation, which failed to flag the conflict. I rewrote `overlaps_with()` to compare
start/end minute ranges instead of exact-time equality, then confirmed the test passed.

A second example was recurrence: my first pass just reset a completed task's `completed` flag back to
`False` so it "reappeared" the next day. That's simpler, but it silently loses history (you can't tell a
task happened yesterday) and doesn't actually advance the date. I rejected that approach in favor of
`Task.next_occurrence()` creating a brand-new `Task` dated `+1 day`/`+1 week`, which keeps the completed
original as a record and gives the new instance its own identity, closer to how a real calendar app
handles recurrence.

**c. AI strategy**

The most effective AI-assistant features for this project were inline chat-with-file-context (attaching
`pawpal_system.py` directly rather than re-describing it in prose) and using separate chat sessions per
phase (one for design/skeletons, a fresh one for the algorithmic layer, and another for testing). Keeping
them separate mattered because a single long-running chat started anchoring on earlier, since-changed
decisions (e.g., still assuming the old "reset the flag" recurrence approach after I'd moved to
`next_occurrence()`); a clean session forced me to re-state the current design accurately, which caught
that kind of drift early instead of propagating it into new code.

---

## 4. Testing and Verification

**a. What you tested**

The two required behaviors (`mark_complete()` changing a task's status, and adding a task increasing a
pet's task count) plus the core algorithmic behaviors from Phase 4/5: priority/time sorting order
(including tasks added deliberately out of order), time-budget filtering (including a zero-budget edge
case), filtering by pet and by completion status, conflict detection (overlapping, exact-duplicate,
non-overlapping, back-to-back, cross-pet, and different-date tasks), and recurrence (completing a DAILY
task creates one dated `+1 day`, WEEKLY creates one dated `+1 week`, ONCE creates nothing). I also tested
the two stretch features: next-available-slot lookup and JSON save/load round-tripping. These mattered
because the sorting/filtering/conflict/recurrence logic is the actual "smart" part of the system: if it's
wrong, the app still runs without crashing, but it quietly gives the owner a bad or misleading plan.

**b. Confidence**

I'm fairly confident the core scheduling logic is correct: 36 tests pass, including edge cases like a
zero-minute time budget, back-to-back tasks that shouldn't be flagged as conflicting, and tasks on
different dates that shouldn't conflict even at the same time-of-day. With more time I'd add tests for:
tasks that span midnight, an owner with zero pets calling `build_daily_plan()`, and a three-way conflict
(three tasks all overlapping the same time slot) to make sure `find_conflicts()` reports all pairs and not
just adjacent ones.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with keeping `Scheduler` separate from `Owner`/`Pet`/`Task`. It made testing much easier
(I could test the "dumb" data classes and the "smart" scheduling algorithms independently) and it meant
Phase 3 (connecting to Streamlit) only required wiring `Scheduler` calls to buttons, not rewriting any
logic to work with the UI.

**b. What you would improve**

If I had another iteration, I'd make the time-budget filtering configurable. Right now it's a strict
greedy cutoff, but a real owner might want to say "always include medications no matter what," which would
mean some tasks should ignore the time budget entirely.

**c. Key takeaway**

The most important thing I learned is that letting AI draft code *before* I'd nailed down the design led to
worse results than sketching the classes and their responsibilities myself first, then using AI to
scaffold and fill in from that. When I started with a clear UML and plain-language description of what each
class was responsible for, the AI's generated code needed far fewer corrections than when I asked it to
"just build a pet scheduler" from scratch.

Being the "lead architect" meant my job was never to accept the first working version. It was to decide
*which* working version was right for this system: greedy time-budget filtering over an optimal-but-opaque
solver, overlap-based conflict detection over exact-time matching, and new-task recurrence over
flag-resetting. AI could generate all four options quickly; deciding which one actually served a pet
owner, and verifying each with a test that would fail if I was wrong, was the part that stayed on me.
