import wfdb
import numpy as np


RECORD_PATH = "data/picsdb/infant1_resp"

print("Loading PICSDB respiration annotations...")

annotations = wfdb.rdann(
    RECORD_PATH,
    "resp"
)

samples = np.asarray(
    annotations.sample,
    dtype=int
)

fs = annotations.fs

times = samples / fs

print("\n======================================")
print("RESPIRATION REFERENCE ANALYSIS")
print("======================================")

print("Total annotations:", len(samples))
print("Sampling frequency:", fs)

# ------------------------------------------------------------
# Basic interval analysis
# ------------------------------------------------------------

intervals = np.diff(times)

print("\n======================================")
print("RAW ANNOTATION INTERVALS")
print("======================================")

print("Minimum:", round(np.min(intervals), 4), "sec")
print("Median:", round(np.median(intervals), 4), "sec")
print("Mean:", round(np.mean(intervals), 4), "sec")
print("Maximum:", round(np.max(intervals), 4), "sec")

# ------------------------------------------------------------
# Interval distribution
# ------------------------------------------------------------

ranges = [
    (0, 0.1),
    (0.1, 0.25),
    (0.25, 0.5),
    (0.5, 1.0),
    (1.0, 1.5),
    (1.5, 2.0),
    (2.0, 3.0),
    (3.0, 5.0),
    (5.0, 10.0),
    (10.0, 20.0),
    (20.0, float("inf")),
]

print("\n======================================")
print("INTERVAL DISTRIBUTION")
print("======================================")

for low, high in ranges:

    count = np.sum(
        (intervals >= low)
        &
        (intervals < high)
    )

    if np.isinf(high):

        label = f">= {low} sec"

    else:

        label = f"{low} - {high} sec"

    print(
        f"{label:20s}: {count}"
    )

# ------------------------------------------------------------
# Examine selected time windows
# ------------------------------------------------------------

windows = [
    (210, 220),
    (217, 219),
    (500, 510),
    (758, 760),
    (1000, 1010),
]

print("\n======================================")
print("SELECTED WINDOWS")
print("======================================")

for start_min, end_min in windows:

    start_sec = start_min * 60
    end_sec = end_min * 60

    mask = (
        (times >= start_sec)
        &
        (times <= end_sec)
    )

    window_times = times[mask]

    window_intervals = np.diff(
        window_times
    )

    print(
        f"\nWindow: "
        f"{start_min} - {end_min} min"
    )

    print(
        "Annotations:",
        len(window_times)
    )

    if len(window_intervals) > 0:

        print(
            "Interval median:",
            round(
                np.median(
                    window_intervals
                ),
                3
            ),
            "sec"
        )

        print(
            "Interval maximum:",
            round(
                np.max(
                    window_intervals
                ),
                3
            ),
            "sec"
        )

        long_intervals = (
            window_intervals[
                window_intervals >= 10
            ]
        )

        print(
            "Intervals >= 10 sec:",
            len(long_intervals)
        )

        if len(long_intervals) > 0:

            print(
                "Longest intervals:"
            )

            sorted_intervals = np.sort(
                long_intervals
            )[::-1]

            for value in sorted_intervals[:10]:

                print(
                    f"  {value:.2f} sec"
                )

# ------------------------------------------------------------
# Inspect annotations around known apnea event
# ------------------------------------------------------------

print("\n======================================")
print("KNOWN EVENT: AROUND 218 MIN")
print("======================================")

start_sec = 217.5 * 60
end_sec = 219.5 * 60

mask = (
    (times >= start_sec)
    &
    (times <= end_sec)
)

event_times = times[mask]

print(
    "Annotations in window:",
    len(event_times)
)

for i in range(
    min(100, len(event_times))
):

    print(
        f"{i + 1:3d}. "
        f"{event_times[i] / 60:.4f} min"
    )

print("\nAnalysis complete.")