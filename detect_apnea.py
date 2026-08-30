import wfdb
import numpy as np
from scipy.signal import butter, sosfiltfilt, find_peaks


# ============================================================
# SETTINGS
# ============================================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

APNEA_THRESHOLD = 20.0

MIN_BREATH_DISTANCE = 1.5

PEAK_PROMINENCE_FACTOR = 0.25

MIN_VALID_INTERVAL = 1.0

# ------------------------------------------------------------
# NEW VALIDATION SETTINGS
# ------------------------------------------------------------

# We do NOT require every long interval to have suppression.
# A genuine apnea may have weak/variable amplitude evidence.

SUPPRESSION_STRONG = 0.45
SUPPRESSION_WEAK = 0.75

BEFORE_WINDOW = 10.0
AFTER_WINDOW = 10.0

# Do not merge events aggressively.
MERGE_GAP = 1.0

# Maximum extension allowed around a long interval
MAX_EVENT_EXTENSION = 5.0


# ============================================================
# LOAD SIGNAL
# ============================================================

print("Loading respiration signal...")

record = wfdb.rdrecord(
    RECORD_PATH,
    physical=False
)

signal = record.d_signal

if signal is None:
    signal = record.p_signal

signal = np.asarray(
    signal[:, 0],
    dtype=np.float64
)

total_samples = len(signal)

print("Total samples:", total_samples)
print("Sampling frequency:", FS)
print(
    "Duration:",
    round(total_samples / FS / 60, 1),
    "minutes"
)


# ============================================================
# FILTER
# ============================================================

print()
print("Filtering respiration signal...")

signal = np.nan_to_num(
    signal,
    nan=0.0,
    posinf=0.0,
    neginf=0.0
)

signal = signal - np.median(signal)

sos = butter(
    4,
    [0.05, 2.0],
    btype="bandpass",
    fs=FS,
    output="sos"
)

filtered = sosfiltfilt(
    sos,
    signal
)


# ============================================================
# RMS AMPLITUDE
# ============================================================

def rms_amplitude(data):

    if len(data) == 0:
        return 0.0

    centered = (
        data - np.median(data)
    )

    return float(
        np.sqrt(
            np.mean(
                centered ** 2
            )
        )
    )


# ============================================================
# CHUNKED PEAK DETECTION
# ============================================================

print()
print("Detecting respiration peaks...")

chunk_seconds = 600
chunk_samples = chunk_seconds * FS

all_peaks = []

start = 0
chunk_number = 0

while start < total_samples:

    chunk_number += 1

    end = min(
        total_samples,
        start + chunk_samples
    )

    chunk = filtered[start:end]

    median_value = np.median(chunk)

    mad = np.median(
        np.abs(
            chunk - median_value
        )
    )

    robust_std = 1.4826 * mad

    if robust_std <= 1e-12:
        robust_std = np.std(chunk)

    if robust_std <= 1e-12:
        robust_std = 1.0

    prominence = (
        PEAK_PROMINENCE_FACTOR
        * robust_std
    )

    distance = int(
        MIN_BREATH_DISTANCE * FS
    )

    peaks, _ = find_peaks(
        chunk,
        distance=distance,
        prominence=prominence
    )

    peaks = peaks + start

    all_peaks.extend(
        peaks.tolist()
    )

    print(
        f"Chunk {chunk_number}: "
        f"{start / FS / 60:.1f} - "
        f"{end / FS / 60:.1f} min | "
        f"peaks: {len(peaks)}"
    )

    start = end


# ============================================================
# CLEAN PEAKS
# ============================================================

peaks = np.asarray(
    all_peaks,
    dtype=np.int64
)

peaks = np.unique(peaks)
peaks.sort()

print()
print(
    "Detected respiration peaks:",
    len(peaks)
)

if len(peaks) < 2:
    raise SystemExit(
        "Not enough respiration peaks."
    )


# ============================================================
# RESPIRATORY INTERVALS
# ============================================================

intervals = np.diff(peaks) / FS

valid_mask = (
    intervals >= MIN_VALID_INTERVAL
)

valid_intervals = intervals[
    valid_mask
]

print()
print("======================================")
print("RESPIRATORY INTERVAL ANALYSIS")
print("======================================")

print(
    "Total intervals:",
    len(intervals)
)

print(
    "Valid intervals:",
    len(valid_intervals)
)

print(
    "Median interval:",
    round(
        np.median(valid_intervals),
        3
    ),
    "sec"
)

print(
    "Maximum interval:",
    round(
        np.max(valid_intervals),
        3
    ),
    "sec"
)

print(
    "Intervals >= 20 sec:",
    np.sum(
        valid_intervals >= APNEA_THRESHOLD
    )
)


# ============================================================
# SUPPRESSION ANALYSIS
# ============================================================

def calculate_suppression(
    start_time,
    end_time
):

    event_start = int(
        start_time * FS
    )

    event_end = int(
        end_time * FS
    )

    before_start = max(
        0,
        event_start -
        int(BEFORE_WINDOW * FS)
    )

    after_end = min(
        total_samples,
        event_end +
        int(AFTER_WINDOW * FS)
    )

    before_signal = filtered[
        before_start:event_start
    ]

    during_signal = filtered[
        event_start:event_end
    ]

    after_signal = filtered[
        event_end:after_end
    ]

    before_amp = rms_amplitude(
        before_signal
    )

    during_amp = rms_amplitude(
        during_signal
    )

    after_amp = rms_amplitude(
        after_signal
    )

    if before_amp <= 1e-12:
        ratio = 1.0
    else:
        ratio = (
            during_amp /
            before_amp
        )

    return (
        before_amp,
        during_amp,
        after_amp,
        ratio
    )


# ============================================================
# FIND LONG INTERVALS
# ============================================================

print()
print("======================================")
print("LONG INTERVAL CANDIDATES")
print("======================================")

long_candidates = []

for i, interval in enumerate(intervals):

    if interval < APNEA_THRESHOLD:
        continue

    start_time = peaks[i] / FS
    end_time = peaks[i + 1] / FS

    (
        before_amp,
        during_amp,
        after_amp,
        ratio
    ) = calculate_suppression(
        start_time,
        end_time
    )

    long_candidates.append(
        {
            "start": start_time,
            "end": end_time,
            "duration": interval,
            "before_amp": before_amp,
            "during_amp": during_amp,
            "after_amp": after_amp,
            "suppression_ratio": ratio
        }
    )

print(
    "Long intervals:",
    len(long_candidates)
)


# ============================================================
# VALIDATION
# ============================================================

print()
print("======================================")
print("VALIDATING APNEA CANDIDATES")
print("======================================")

validated_events = []

for candidate in long_candidates:

    duration = candidate["duration"]
    ratio = candidate["suppression_ratio"]

    # --------------------------------------------------------
    # Rule 1:
    # Strong suppression -> accept
    # --------------------------------------------------------

    if ratio <= SUPPRESSION_STRONG:

        candidate["reason"] = "strong_suppression"

        validated_events.append(
            candidate
        )

        continue

    # --------------------------------------------------------
    # Rule 2:
    # Very long interval -> accept even if suppression
    # is imperfect.
    # --------------------------------------------------------

    if duration >= 30.0:

        candidate["reason"] = "long_interval"

        validated_events.append(
            candidate
        )

        continue

    # --------------------------------------------------------
    # Rule 3:
    # Moderate suppression + sufficiently long interval
    # --------------------------------------------------------

    if (
        ratio <= SUPPRESSION_WEAK
        and
        duration >= 22.0
    ):

        candidate["reason"] = "moderate_suppression"

        validated_events.append(
            candidate
        )

        continue


print(
    "Validated apnea candidates:",
    len(validated_events)
)


# ============================================================
# MERGE ONLY OVERLAPPING / NEAR-OVERLAPPING EVENTS
# ============================================================

validated_events.sort(
    key=lambda x: x["start"]
)

merged_events = []

for event in validated_events:

    if not merged_events:

        merged_events.append(
            event.copy()
        )

        continue

    previous = merged_events[-1]

    gap = (
        event["start"]
        - previous["end"]
    )

    # Only merge if practically adjacent.
    if gap <= MERGE_GAP:

        previous["end"] = max(
            previous["end"],
            event["end"]
        )

        previous["duration"] = (
            previous["end"]
            - previous["start"]
        )

        previous["suppression_ratio"] = min(
            previous["suppression_ratio"],
            event["suppression_ratio"]
        )

    else:

        merged_events.append(
            event.copy()
        )


# ============================================================
# REMOVE DUPLICATE / CONTAINED EVENTS
# ============================================================

final_events = []

for event in merged_events:

    contained = False

    for existing in final_events:

        if (
            event["start"] >= existing["start"]
            and
            event["end"] <= existing["end"]
        ):

            contained = True
            break

    if not contained:

        final_events.append(
            event
        )


# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("======================================")
print("FINAL APNEA EVENTS")
print("======================================")

print(
    "Final apnea events:",
    len(final_events)
)

for i, event in enumerate(
    final_events,
    start=1
):

    print()

    print(
        f"Event {i}"
    )

    print(
        f"Start: "
        f"{event['start'] / 60:.2f} min"
    )

    print(
        f"End: "
        f"{event['end'] / 60:.2f} min"
    )

    print(
        f"Duration: "
        f"{event['duration']:.2f} sec"
    )

    print(
        f"Suppression ratio: "
        f"{event['suppression_ratio']:.3f}"
    )

    print(
        f"Reason: "
        f"{event.get('reason', 'unknown')}"
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("======================================")
print("FINAL SUMMARY")
print("======================================")

print(
    "Respiration peaks:",
    len(peaks)
)

print(
    "Valid respiratory intervals:",
    len(valid_intervals)
)

print(
    "Long interval candidates:",
    len(long_candidates)
)

print(
    "Validated apnea events:",
    len(final_events)
)

print()
print(
    "Analysis complete."
)