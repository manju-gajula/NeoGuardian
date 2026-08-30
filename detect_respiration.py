import wfdb
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks


# ==========================================
# SETTINGS
# ==========================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

# We will initially analyze only 5 minutes.
# This keeps the first test fast.
ANALYSIS_MINUTES = 120

# Expected infant respiration range.
# We start conservatively and can tune this later.
MIN_BREATH_INTERVAL = 1.0
MAX_BREATH_INTERVAL = 10.0


# ==========================================
# 1. LOAD RESPIRATION SIGNAL
# ==========================================

print("Loading respiration signal...")

record = wfdb.rdrecord(RECORD_PATH)

resp = record.p_signal[:, 0]

print("Signal loaded successfully!")
print("Total samples:", len(resp))
print("Sampling frequency:", record.fs)


# ==========================================
# 2. SELECT FIRST FEW MINUTES
# ==========================================

samples_to_use = int(ANALYSIS_MINUTES * FS)

resp = resp[:samples_to_use]

time = np.arange(len(resp)) / FS

print("Samples used:", len(resp))
print("Duration:", len(resp) / FS, "seconds")


# ==========================================
# 3. REMOVE DC OFFSET
# ==========================================

resp = resp - np.mean(resp)


# ==========================================
# 4. BANDPASS FILTER
# ==========================================

# Infant respiration is much slower than ECG.
#
# Approximate respiration frequency:
# 0.1 Hz  -> 6 breaths/min
# 1.0 Hz  -> 60 breaths/min
#
# We allow a wider range initially.

lowcut = 0.1
highcut = 0.8

b, a = butter(
    3,
    [lowcut / (FS / 2), highcut / (FS / 2)],
    btype="band"
)

filtered_resp = filtfilt(b, a, resp)


# ==========================================
# 5. NORMALIZE SIGNAL
# ==========================================

filtered_resp = (
    filtered_resp - np.mean(filtered_resp)
) / np.std(filtered_resp)


# ==========================================
# 6. DETECT RESPIRATION PEAKS
# ==========================================

# Minimum distance between detected peaks.
#
# 0.5 sec corresponds to 120 breaths/min.
# This prevents the algorithm from detecting
# tiny fluctuations as separate breaths.

min_distance = int(MIN_BREATH_INTERVAL * FS)

peaks, properties = find_peaks(
    filtered_resp,
    distance=min_distance,
    prominence=0.30
)


# ==========================================
# 7. CALCULATE RESPIRATION INTERVALS
# ==========================================

peak_times = peaks / FS

resp_intervals = np.diff(peak_times)


# ==========================================
# 8. REMOVE UNREALISTIC INTERVALS
# ==========================================

valid_intervals = resp_intervals[
    (resp_intervals >= MIN_BREATH_INTERVAL)
    & (resp_intervals <= MAX_BREATH_INTERVAL)
]


# ==========================================
# 9. CALCULATE RESPIRATION RATE
# ==========================================

if len(valid_intervals) > 0:

    respiration_rates = 60 / valid_intervals

    print("\n======================================")
    print("RESPIRATION ANALYSIS")
    print("======================================")

    print("Detected respiration peaks:", len(peaks))

    print(
        "Valid respiration intervals:",
        len(valid_intervals)
    )

    print(
        "Mean respiration rate:",
        round(np.mean(respiration_rates), 2),
        "breaths/min"
    )

    print(
        "Median respiration rate:",
        round(np.median(respiration_rates), 2),
        "breaths/min"
    )

    print(
        "Minimum respiration rate:",
        round(np.min(respiration_rates), 2),
        "breaths/min"
    )

    print(
        "Maximum respiration rate:",
        round(np.max(respiration_rates), 2),
        "breaths/min"
    )


# ==========================================
# 10. SHOW FIRST 20 INTERVALS
# ==========================================

print("\nFirst 20 respiration intervals:")

print(
    np.round(
        valid_intervals[:20],
        3
    )
)


# ==========================================
# 11. PLOT RESPIRATION SIGNAL
# ==========================================

plt.figure(figsize=(14, 6))

plt.plot(
    time,
    filtered_resp,
    label="Filtered respiration"
)

plt.plot(
    peak_times,
    filtered_resp[peaks],
    "ro",
    markersize=4,
    label="Detected breaths"
)

plt.xlabel("Time (seconds)")
plt.ylabel("Normalized respiration")

plt.title(
    "Infant 1 - Detected Respiration Cycles"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.show()