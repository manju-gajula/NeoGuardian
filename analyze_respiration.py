import wfdb
import numpy as np

record_path = "data/picsdb/infant1_resp"

# Load respiration peak annotations
annotations = wfdb.rdann(record_path, "resp")

# Respiration peak locations
peak_samples = np.array(annotations.sample)

# Sampling frequency
fs = annotations.fs

# Convert peak locations to seconds
peak_times = peak_samples / fs

# Calculate intervals between respiration peaks
resp_intervals = np.diff(peak_times)

print("======================================")
print("RESPIRATION INTERVAL ANALYSIS")
print("======================================")

print("Total respiration peaks:", len(peak_samples))
print("Sampling frequency:", fs, "Hz")

print("\nFirst 20 respiration intervals:")
print(resp_intervals[:20])

print("\nRespiration interval statistics:")

print(
    "Minimum interval:",
    round(np.min(resp_intervals), 3),
    "seconds"
)

print(
    "Maximum interval:",
    round(np.max(resp_intervals), 3),
    "seconds"
)

print(
    "Mean interval:",
    round(np.mean(resp_intervals), 3),
    "seconds"
)

print(
    "Median interval:",
    round(np.median(resp_intervals), 3),
    "seconds"
)

print(
    "90th percentile:",
    round(np.percentile(resp_intervals, 90), 3),
    "seconds"
)

print(
    "95th percentile:",
    round(np.percentile(resp_intervals, 95), 3),
    "seconds"
)

print(
    "99th percentile:",
    round(np.percentile(resp_intervals, 99), 3),
    "seconds"
)

# -----------------------------------------
# Find unusually long respiration intervals
# -----------------------------------------

long_intervals = np.where(resp_intervals > 10)[0]

print(
    "\nIntervals longer than 10 seconds:",
    len(long_intervals)
)

print("\nFirst 20 long intervals:")

for i in long_intervals[:20]:

    print(
        f"Peak {i + 1} → Peak {i + 2}: "
        f"{resp_intervals[i]:.2f} seconds "
        f"at {peak_times[i] / 60:.2f} minutes"
    )