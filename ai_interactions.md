# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

For Challenge 1 (Advanced Algorithmic Capability), I asked the agent to add a third algorithm beyond the
base sorting/filtering/conflict-detection requirements: a "find the next available time slot" function
that, given a desired task duration, scans an owner's existing tasks for a day and returns the earliest
open window long enough to fit a new task, something a pet owner could use when deciding what time to
schedule a new vet appointment or walk.

**What did the agent do?**

The agent added `Scheduler.find_next_available_slot(duration_minutes, for_date, day_start, day_end)` to
`pawpal_system.py`: it filters that day's tasks by date, sorts them chronologically, then walks the gaps
between `day_start` and each task's start time (and after the last task, up to `day_end`), returning the
first gap that's long enough. It also wired the feature into `main.py` (a CLI demo section) and `app.py`
(a "Find next available slot" button), and drafted pytest cases covering a gap between two tasks, a fully
booked day (returns `None`), and an empty day (returns `day_start`).

**What did you have to verify or fix manually?**

The agent's first pytest case for "finds gap between tasks" had the wrong expected answer: it asserted
the slot would be found right after an 8:00–8:30 task, but with a 6:00 AM day-start and nothing scheduled
before 8:00, the correct earliest slot is actually 6:00 AM (a 2-hour-wide gap that already fits the
requested duration). I caught this by running the test and manually tracing the algorithm by hand rather
than trusting the assertion, then rewrote the test with a scenario that actually has no gap before the
first task (back-to-back tasks from day-start through lunch) so the assertion tests what it claims to.

---

## Prompt Comparison (SF11)

*(Not attempted. Challenge 5 requires running the same prompt through two different AI models/tools and
comparing their output. I didn't have access to a second model in this environment to do an honest,
non-fabricated comparison, so I left this section blank rather than invent output I never actually got
from a second model.)*
