import wfdb
import numpy as np

record_path = "data/picsdb/infant1_ecg"

# Load R-peak annotations
rpeaks = wfdb.rdann(record_path, "qrsc")

fs = 250

peak_samples = np.array(rpeaks.sample)

# Calculate R-R intervals
rr_intervals = np.diff(peak_samples) / fs

# Calculate heart rate
heart_rate = 60 / rr_intervals

print("R-peak analysis completed!")
print("Total R-peaks:", len(peak_samples))

print("\nFirst 10 heart-rate values:")
print(heart_rate[:10])

print("\nHeart-rate statistics:")
print("Minimum HR:", np.min(heart_rate))
print("Maximum HR:", np.max(heart_rate))
print("Mean HR:", np.mean(heart_rate))
print("Median HR:", np.median(heart_rate))

# Find unusually long R-R intervals
long_rr = np.where(rr_intervals > 1.5)[0]

print("\nNumber of R-R intervals greater than 1.5 seconds:",
      len(long_rr))

print("\nFirst 10 unusually long intervals:")

for i in long_rr[:10]:
    print(
        "R-peak pair:",
        i,
        "to",
        i + 1,
        "| RR:",
        round(rr_intervals[i], 3),
        "seconds",
        "| HR:",
        round(heart_rate[i], 2),
        "BPM"
    )