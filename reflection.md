# PawPal+ Project Reflection

## 1. System design

**a. Initial design**

I started with four classes. Owner and Pet are dataclasses that hold info about the person and their animals. Task is also a dataclass -- it stores a care activity (like a walk or feeding) with a duration, priority level from 1 to 5, and which pet it's for. Scheduler is the only non-dataclass; it takes in an Owner, looks at all the Tasks, and figures out which ones fit into the owner's available time each day.

I went with dataclasses because they handle `__init__` and `__repr__` for free, and I wanted the data objects to stay simple. Keeping the scheduling logic in its own class means I can change how prioritization works without touching the data layer.

**b. Design changes**

The big one was a circular reference bug that didn't show up until I ran the Streamlit app. Owner has a list of pets, and each Pet has a reference back to its owner. Python dataclasses auto-generate `__eq__` that compares every field. So when Streamlit tried to compare Pet objects in a selectbox, it compared the `owner` field, which compared `pets`, which compared each Pet's `owner`, and so on forever. The app would crash with a max recursion depth error the moment you tried to add a task.

The fix was marking those cross-reference fields with `compare=False` and `repr=False`. Breaks the cycle, keeps the relationship intact.

I also added `__post_init__` validation on Task to reject priorities outside 1-5 and zero/negative durations. Better to fail loud at object creation than silently schedule garbage data.

---

## 2. Scheduling logic and tradeoffs

**a. Constraints and priorities**

Three things drive the schedule. First, the owner's available time in minutes per day -- that's a hard ceiling, nothing goes over it. Second, task priority. The scheduler sorts highest-priority tasks first, so medication doesn't get bumped by a grooming session. Third, completion status. If a task is already done, it's out.

Time felt like the obvious top constraint since you can't manufacture more of it. Priority came next because pet health stuff (meds, feeding) should never lose to optional activities.

**b. Tradeoffs**

It's a greedy algorithm. Sort by priority descending, break ties by shortest duration first, then fill up the day until time runs out.

The downside: it doesn't always maximize how many tasks get done. Say you have a 60-minute priority-5 task and two 30-minute priority-4 tasks, with 90 minutes available. The scheduler picks the priority-5 task first, then one of the priority-4 tasks. It won't skip the high-priority one to fit both smaller ones, even though that would fill the schedule perfectly.

Honestly, for pet care that's the right call. You don't want an algorithm that drops someone's dog medication to squeeze in two play sessions. When priorities tie, the shorter-task-first rule helps pack more in, which is a reasonable compromise.

---

## 3. AI collaboration

**a. How you used AI**

I used Claude Code throughout. Early on I had it review the class structure and it flagged the circular Owner-Pet reference as a potential problem. I didn't fully appreciate why until the app actually crashed, but having that warning meant I knew where to look.

For implementation, it helped scaffold the dataclasses and the scheduling algorithm. I leaned on it most for the `__post_init__` validation and the `explain_reasoning()` method, since those are tedious to get right from scratch.

It also wrote the first draft of the pytest suite. I wouldn't have thought to test zero available time or what happens when all tasks are already completed. Those edge cases seemed obvious in hindsight but weren't on my radar.

The debugging was where it really paid off. When the app hit max recursion depth, I didn't immediately connect it to the dataclass comparison. Working through it with the AI got me to the `compare=False` fix in maybe 10 minutes instead of an hour of staring at stack traces.

Asking "what could go wrong with this design" turned out to be a better prompt than "write me a scheduler."

**b. Judgment and verification**

The first version of `explain_reasoning()` that the AI produced was full of technical language -- stuff about greedy algorithms and sorting complexity. Nobody using a pet care app wants to read that. They want to know if their dog's medication made the cut.

I rewrote it to show plain numbers: how many tasks got scheduled, how much time is used, what got skipped and why. I tested it by just reading the output and asking myself if it made sense without any CS background. It did after the rewrite.

---

## 4. Testing and verification

**a. What you tested**

The test file has six groups of tests covering different parts of the system.

Data model tests check that Owner, Pet, and Task objects create correctly, that validation rejects bad input (priority of 6, duration of 0), and that the bidirectional Owner-Pet relationship works without breaking anything.

Scheduling tests verify the prioritization order, that the plan stays within the time limit, that completed tasks get excluded, and that edge cases like no tasks or zero available time don't blow up.

There are also filter tests (tasks by pet, by type, incomplete only), time based tests (scheduled time validation, end time math, conflict detection between overlapping tasks), recurring task tests (daily/weekly recurrence, one-time tasks refusing to recur), and one integration test that runs a full workflow from creating an owner through generating and regenerating a schedule.

The scheduling and conflict detection tests were the most important to get right. If the prioritization logic is off, every schedule the app produces is wrong. If conflict detection misses overlapping tasks, the user gets a broken plan with no warning.

**b. Confidence**

Pretty confident for the scope we're targeting. All tests pass, the Streamlit UI behaves correctly when I click around manually, and the recursion bug is fixed.

What I haven't tested: large task sets (100+), race conditions in the UI (adding a task while generating a schedule), and weird input like extremely long durations or unicode pet names. Those would be next on the list.

---

## 5. Reflection

**a. What went well**

The separation between data and logic turned out well. When the recursion bug hit, the fix was entirely in the dataclass layer. I didn't have to touch the scheduler or the UI code. That only works if the layers aren't leaking into each other, so I was glad the architecture held up under a real bug.

Having tests already written before I fixed the recursion issue was also nice. I could make the change and immediately confirm nothing else broke.

**b. What you would improve**

The greedy scheduler gets the job done but isn't optimal. A knapsack-style dynamic programming approach would find better combinations of tasks for a given time budget. I'd also add real time slots (like 9:00-9:30 AM) instead of just an ordered list, since the conflict detection code is already there but only works with manually set times.

Persistence is the other big gap. Everything disappears on page refresh. Even writing to a JSON file would make it usable across sessions.

The Owner preferences dictionary exists but does nothing yet. Feeding things like "morning person" into the scheduling order would make results feel less generic.

**c. Key takeaway**

Catching bugs at the design stage is way cheaper than finding them in a running app. The circular reference thing could have been a nightmare if I'd built the whole UI first and then discovered that every selectbox crashed. Instead, the AI flagged it during design review and the fix was two lines of code.

That changed how I think about using AI on projects. Asking it to poke holes in a design before writing code is more useful than asking it to write the code faster.
