import wfdb
import numpy as np

record_path = "data/picsdb/infant1_ecg"

# Sampling frequency
fs = 250

# Bradycardia threshold
BRADYCARDIA_HR = 100

# Minimum duration
MIN_DURATION = 1.2

# Load R-peak annotations
rpeaks = wfdb.rdann(record_path, "qrsc")
peak_samples = np.array(rpeaks.sample)

# Calculate R-R intervals
rr_intervals = np.diff(peak_samples) / fs

# Calculate heart rate
heart_rate = 60 / rr_intervals

# Time corresponding to each HR measurement
hr_times = peak_samples[1:] / fs

# -----------------------------------------
# Find potential bradycardia intervals
# -----------------------------------------

brady_mask = heart_rate < BRADYCARDIA_HR

# Find consecutive low-HR measurements
events = []

start = None

for i, is_brady in enumerate(brady_mask):

    if is_brady and start is None:
        start = i

    elif not is_brady and start is not None:

        end = i - 1

        duration = hr_times[end] - hr_times[start]

        if duration >= MIN_DURATION:
            events.append(
                (
                    hr_times[start],
                    hr_times[end],
                    duration
                )
            )

        start = None

# Handle an event that continues to the end
if start is not None:

    end = len(heart_rate) - 1

    duration = hr_times[end] - hr_times[start]

    if duration >= MIN_DURATION:
        events.append(
            (
                hr_times[start],
                hr_times[end],
                duration
            )
        )

# -----------------------------------------
# Display results
# -----------------------------------------

print("======================================")
print("BASELINE BRADYCARDIA DETECTOR")
print("======================================")

print("Total R-peaks:", len(peak_samples))
print("Total HR measurements:", len(heart_rate))

print(
    "\nBradycardia threshold:",
    BRADYCARDIA_HR,
    "BPM"
)

print(
    "Minimum duration:",
    MIN_DURATION,
    "seconds"
)

print(
    "\nDetected bradycardia candidate events:",
    len(events)
)

print("\nFirst 20 detected events:")
print("--------------------------------------")

for i, event in enumerate(events[:20]):

    start_time, end_time, duration = event

    print(
        f"Event {i + 1}: "
        f"{start_time / 60:.2f} min → "
        f"{end_time / 60:.2f} min "
        f"(duration: {duration:.2f} sec)"
    )