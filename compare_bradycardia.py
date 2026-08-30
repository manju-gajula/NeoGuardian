import wfdb
import numpy as np
import matplotlib.pyplot as plt

record_path = "data/picsdb/infant1_ecg"

# Sampling frequency
fs = 250

# Load R-peak annotations
rpeaks = wfdb.rdann(record_path, "qrsc")
peak_samples = np.array(rpeaks.sample)

# Load bradycardia annotations
brady = wfdb.rdann(record_path, "atr")
brady_samples = np.array(brady.sample)

# -----------------------------------------
# Select bradycardia event 9
# -----------------------------------------

event_number = 9
brady_sample = brady_samples[event_number - 1]

# -----------------------------------------
# Calculate R-R intervals and heart rate
# -----------------------------------------

rr_intervals = np.diff(peak_samples) / fs

heart_rate = 60 / rr_intervals

# Time of each heart-rate measurement
hr_times = peak_samples[1:] / fs

# -----------------------------------------
# Select 30-second window
# -----------------------------------------

window_seconds = 15

start_time = brady_sample / fs - window_seconds
end_time = brady_sample / fs + window_seconds

mask = (
    (hr_times >= start_time) &
    (hr_times <= end_time)
)

window_times = hr_times[mask]
window_hr = heart_rate[mask]

# -----------------------------------------
# Plot
# -----------------------------------------

plt.figure(figsize=(14, 5))

plt.plot(
    window_times,
    window_hr,
    marker="o",
    markersize=3,
    label="Calculated Heart Rate"
)

# Bradycardia threshold
plt.axhline(
    100,
    linestyle="--",
    label="Bradycardia threshold (100 BPM)"
)

# PICSDB annotation
plt.axvline(
    brady_sample / fs,
    linestyle="--",
    label="PICSDB bradycardia onset"
)

plt.title(
    "Infant 1 - Heart Rate Around Bradycardia Event 9"
)

plt.xlabel("Time (seconds)")
plt.ylabel("Heart Rate (BPM)")

plt.legend()
plt.grid(True)

plt.show()