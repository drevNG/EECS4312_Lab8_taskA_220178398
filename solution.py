## Student Name:
## Student ID:

"""
Task A: Appointment Timeslot Recommender (Stub)

In this lab, you will design and implement an Appointment Slot Recommender using an LLM assistant
as your primary programming collaborator.

You are asked to implement a Python module that recommends available meeting slots within a
defined working window.

The system must:
  • Accept working hours (start and end time).
  • Accept a list of existing busy intervals.
  • Accept a required meeting duration.
  • Accept an optional buffer time between meetings.
  • Optionally restrict suggestions to a candidate time window.
  • Return chronologically ordered appointment slots that satisfy all constraints.

The system must ensure that:
  • Suggested slots fall within working hours.
  • Suggested slots do not overlap busy intervals.
  • Buffer time is respected when evaluating availability.
  • Output ordering is deterministic under identical inputs.

The module must preserve the following invariants:
  • Returned slots must be at least as long as the required duration.
  • No returned slot may violate buffer constraints.
  • The returned list must reflect the current system state.

The system must correctly handle non-trivial scenarios such as:
  • Adjacent busy intervals.
  • Very small gaps between meetings.
  • Buffers eliminating otherwise valid availability.
  • Overlapping or unsorted busy intervals.
  • A meeting duration longer than any available gap.
  • No availability within the working window.

Output:
  The output consists of the next N valid appointment suggestions in chronological order.
  Behavior must be deterministic under ties (if any).

See the lab handout for full requirements.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple


# ---------------- Data Models ----------------

@dataclass(frozen=True)
class TimeWindow:
    """
    A daily time window.
    Assumption (unless stated otherwise in handout): non-wrapping window where start < end.
    """
    start: time
    end: time


@dataclass(frozen=True)
class BusyInterval:
    """
    A busy interval on the given day.
    Invariant: start < end
    """
    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    """
    A recommended appointment slot.

    start_time is a time-of-day within the working window.
    Deterministic ordering: sort by start_time ascending.
    """
    start_time: time


class InfeasibleSchedule(Exception):
    """Raised when no valid slots can be produced (if required by handout)."""
    pass


# ---------------- Core Function ----------------

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:
    """
    Suggest up to the next n valid appointment slots (start times) for the given day.

    Args:
        day: the calendar day for which to suggest slots.
        working_hours: the allowed working window for meetings (start < end).
        busy_intervals: list of busy time intervals (may be overlapping / unsorted).
        duration: required meeting length (must be > 0).
        n: maximum number of slot suggestions to return (n >= 0).
        buffer: optional buffer time required between meetings (buffer >= 0).
        candidate_window: optional extra restriction on suggestions (must lie within this window too).

    Returns:
        A list of Slot objects, sorted by start_time ascending, deterministic under identical inputs.
        If no suitable time slots are available, return an empty list.

    Notes:
        - Suggested slots must fall within working_hours (and candidate_window if provided).
        - Suggested slots must not overlap busy_intervals, considering buffer time.
        - You are free to choose internal representation; inputs use time-of-day.
        - See lab handout for required slot granularity (e.g., 5-min/15-min steps), if any.
    """

    ##################################################################
    # TODO: Implement as per lab handout requirements and constraints.
    ##################################################################
    
    #raise NotImplementedError("suggest_slots has not been implemented yet")
    def time_to_minutes(t: time) -> int:
        return t.hour * 60 + t.minute

    def minutes_to_time(m: int) -> time:
        h = m // 60
        m = m % 60
        return time(hour=h, minute=m)

    def intersect(a_start, a_end, b_start, b_end):
        s = max(a_start, b_start)
        e = min(a_end, b_end)
        if s < e:
            return (s, e)
        return None

    # ---------- Validation ----------

    if duration <= timedelta(0) or n <= 0:
        return []

    duration_min = int(duration.total_seconds() // 60)
    buffer_min = int(buffer.total_seconds() // 60)

    # ---------- Determine effective scheduling window ----------

    work_start = time_to_minutes(working_hours.start)
    work_end = time_to_minutes(working_hours.end)

    if candidate_window:
        cand_start = time_to_minutes(candidate_window.start)
        cand_end = time_to_minutes(candidate_window.end)

        window = intersect(work_start, work_end, cand_start, cand_end)
        if window is None:
            return []

        sched_start, sched_end = window
    else:
        sched_start, sched_end = work_start, work_end

    # ---------- Preprocess busy intervals ----------

    intervals = []

    for b in busy_intervals:

        b_start = time_to_minutes(b.start)
        b_end = time_to_minutes(b.end)

        # Clip to working window
        clipped = intersect(b_start, b_end, sched_start, sched_end)
        if not clipped:
            continue

        s, e = clipped

        # Apply buffer
        s -= buffer_min
        e += buffer_min

        # Clip again to scheduling window
        s = max(s, sched_start)
        e = min(e, sched_end)

        if s < e:
            intervals.append((s, e))

    # ---------- Sort and merge intervals ----------

    intervals.sort()

    merged = []
    for s, e in intervals:
        if not merged:
            merged.append([s, e])
        else:
            last_s, last_e = merged[-1]
            if s <= last_e:
                merged[-1][1] = max(last_e, e)
            else:
                merged.append([s, e])

    # ---------- Compute gaps ----------

    gaps = []

    prev_end = sched_start

    for s, e in merged:
        if prev_end < s:
            gaps.append((prev_end, s))
        prev_end = max(prev_end, e)

    if prev_end < sched_end:
        gaps.append((prev_end, sched_end))

    # ---------- Generate slots (1-minute sliding window) ----------

    results = []

    for g_start, g_end in gaps:

        start = g_start
        while start + duration_min <= g_end:

            results.append(Slot(start_time=minutes_to_time(start)))

            if len(results) >= n:
                return results

            start += 1

    return results
