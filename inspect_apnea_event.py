import wfdb
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt, find_peaks


# ==========================================
# SETTINGS
# ==========================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

# Target region from our earlier analysis
EVENT_TIME_MINUTES = 218.0

# Analyze 2 minutes around the target
WINDOW_BEFORE_SECONDS = 30
WINDOW_AFTER_SECONDS = 90

# Respiration filter
LOWCUT = 0.1
HIGHCUT = 0.8

# Breath detection
MIN_BREATH_INTERVAL = 1.5
PROMINENCE = 0.60

# Candidate pause thresholds
SHORT_PAUSE_THRESHOLD = 10.0
APNEA_THRESHOLD = 20.0


# ==========================================
# CALCULATE WINDOW
# ==========================================

event_time_seconds = (
    EVENT_TIME_MINUTES * 60
)

start_seconds = (
    event_time_seconds
    - WINDOW_BEFORE_SECONDS
)

duration_seconds = (
    WINDOW_BEFORE_SECONDS
    + WINDOW_AFTER_SECONDS
)

start_sample = int(
    start_seconds * FS
)

end_sample = int(
    (start_seconds + duration_seconds)
    * FS
)


print("Loading respiration signal...")

record = wfdb.rdrecord(
    RECORD_PATH,
    sampfrom=start_sample,
    sampto=end_sample,
    channels=[0]
)

resp = record.p_signal[:, 0]


print("Signal loaded successfully!")

print("\n======================================")
print("TARGETED RESPIRATION EVENT ANALYSIS")
print("======================================")

print(
    "Target event:",
    EVENT_TIME_MINUTES,
    "minutes"
)

print(
    "Window start:",
    round(start_seconds, 2),
    "seconds"
)

print(
    "Window duration:",
    round(len(resp) / FS, 2),
    "seconds"
)

print(
    "Window absolute time:",
    round(start_seconds / 60, 2),
    "to",
    round((start_seconds + len(resp) / FS) / 60, 2),
    "minutes"
)


# ==========================================
# FILTER
# ==========================================

nyquist = FS / 2

low = LOWCUT / nyquist
high = HIGHCUT / nyquist

sos = butter(
    4,
    [low, high],
    btype="band",
    output="sos"
)

filtered_resp = sosfiltfilt(
    sos,
    resp
)


# ==========================================
# NORMALIZE
# ==========================================

filtered_resp = (
    filtered_resp
    - np.mean(filtered_resp)
)

std = np.std(filtered_resp)

if std > 0:
    filtered_resp = (
        filtered_resp / std
    )


# ==========================================
# DETECT BREATHS
# ==========================================

min_distance = int(
    MIN_BREATH_INTERVAL * FS
)

peaks, properties = find_peaks(
    filtered_resp,
    distance=min_distance,
    prominence=PROMINENCE
)

peak_times_relative = (
    peaks / FS
)

peak_times_absolute = (
    start_seconds
    + peak_times_relative
)

intervals = np.diff(
    peak_times_relative
)


# ==========================================
# RESULTS
# ==========================================

print("\n======================================")
print("BREATH DETECTION")
print("======================================")

print(
    "Detected breaths:",
    len(peaks)
)

print(
    "Valid intervals:",
    len(intervals)
)


if len(intervals) > 0:

    print("\nAll respiratory intervals:")

    for i, interval in enumerate(
        intervals,
        start=1
    ):

        print(
            f"{i:2d}. "
            f"{interval:.2f} seconds"
        )


# ==========================================
# FIND LONG PAUSES
# ==========================================

short_pause_indices = np.where(
    intervals >= SHORT_PAUSE_THRESHOLD
)[0]

apnea_indices = np.where(
    intervals >= APNEA_THRESHOLD
)[0]


print("\n======================================")
print("RESPIRATORY PAUSE CHECK")
print("======================================")

print(
    "Pauses >= 10 seconds:",
    len(short_pause_indices)
)

print(
    "Pauses >= 20 seconds:",
    len(apnea_indices)
)


# ==========================================
# PRINT 10+ SECOND PAUSES
# ==========================================

if len(short_pause_indices) > 0:

    print("\nPauses >= 10 seconds:")

    for number, i in enumerate(
        short_pause_indices,
        start=1
    ):

        start_time = (
            peak_times_absolute[i]
        )

        end_time = (
            peak_times_absolute[i + 1]
        )

        duration = intervals[i]

        print(
            f"{number}. "
            f"{start_time / 60:.2f} min → "
            f"{end_time / 60:.2f} min | "
            f"{duration:.2f} seconds"
        )

else:

    print(
        "\nNo pauses >= 10 seconds found."
    )


# ==========================================
# PRINT 20+ SECOND PAUSES
# ==========================================

if len(apnea_indices) > 0:

    print("\nPotential apnea-duration pauses:")

    for number, i in enumerate(
        apnea_indices,
        start=1
    ):

        start_time = (
            peak_times_absolute[i]
        )

        end_time = (
            peak_times_absolute[i + 1]
        )

        duration = intervals[i]

        print(
            f"{number}. "
            f"{start_time / 60:.2f} min → "
            f"{end_time / 60:.2f} min | "
            f"{duration:.2f} seconds"
        )

else:

    print(
        "\nNo pauses >= 20 seconds found."
    )


# ==========================================
# PLOT
# ==========================================

time = (
    np.arange(len(filtered_resp))
    / FS
)

plt.figure(
    figsize=(15, 6)
)

plt.plot(
    time,
    filtered_resp,
    label="Filtered respiration"
)

plt.plot(
    peak_times_relative,
    filtered_resp[peaks],
    "ro",
    markersize=5,
    label="Detected breaths"
)


# Mark 10-second pauses

for i in short_pause_indices:

    x1 = peak_times_relative[i]
    x2 = peak_times_relative[i + 1]

    plt.axvspan(
        x1,
        x2,
        alpha=0.25
    )


# Mark 20-second pauses differently

for i in apnea_indices:

    x1 = peak_times_relative[i]
    x2 = peak_times_relative[i + 1]

    plt.axvspan(
        x1,
        x2,
        alpha=0.40
    )


plt.axvline(
    WINDOW_BEFORE_SECONDS,
    linestyle="--",
    label="Reference event time"
)


plt.xlabel(
    "Time within window (seconds)"
)

plt.ylabel(
    "Normalized respiration"
)

plt.title(
    "Infant 1 - RESP Around 218 Minutes"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.show()