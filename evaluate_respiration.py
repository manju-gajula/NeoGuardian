import wfdb
import numpy as np
from scipy.signal import butter, sosfiltfilt, find_peaks


# ============================================================
# SETTINGS
# ============================================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

PAUSE_THRESHOLD = 10.0
APNEA_THRESHOLD = 20.0

MIN_BREATH_DISTANCE = 1.5
PEAK_PROMINENCE_FACTOR = 0.25
MIN_VALID_INTERVAL = 1.0

MERGE_GAP = 5.0

# Matching tolerance between detected and reference events
EVENT_MATCH_TOLERANCE = 10.0


# ============================================================
# LOAD RESPIRATION SIGNAL
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

signal = np.nan_to_num(
    signal,
    nan=0.0,
    posinf=0.0,
    neginf=0.0
)

total_samples = len(signal)

print(
    "Total samples:",
    total_samples
)

print(
    "Sampling frequency:",
    FS
)

print(
    "Duration:",
    round(total_samples / FS / 60, 1),
    "minutes"
)


# ============================================================
# FILTER RESPIRATION
# ============================================================

print()
print("Filtering respiration signal...")

signal = (
    signal
    - np.median(signal)
)

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
# PEAK DETECTION
# SAME METHOD AS detect_apnea.py
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
        f"Processing chunk {chunk_number}: "
        f"{start / FS / 60:.1f} - "
        f"{end / FS / 60:.1f} min"
    )

    start = end


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


# ============================================================
# DETECT RESPIRATORY PAUSES
# ============================================================

intervals = (
    np.diff(peaks) / FS
)

candidate_pauses = []

for i, interval in enumerate(intervals):

    if interval < MIN_VALID_INTERVAL:
        continue

    if interval >= PAUSE_THRESHOLD:

        pause_start = (
            peaks[i] / FS
        )

        pause_end = (
            peaks[i + 1] / FS
        )

        candidate_pauses.append(
            [
                pause_start,
                pause_end
            ]
        )


# ============================================================
# MERGE NEARBY PAUSES
# ============================================================

merged_pauses = []

for start_time, end_time in candidate_pauses:

    if not merged_pauses:

        merged_pauses.append(
            [
                start_time,
                end_time
            ]
        )

        continue

    previous = merged_pauses[-1]

    gap = (
        start_time
        - previous[1]
    )

    if gap <= MERGE_GAP:

        previous[1] = max(
            previous[1],
            end_time
        )

    else:

        merged_pauses.append(
            [
                start_time,
                end_time
            ]
        )


# ============================================================
# SELECT APNEA EVENTS
# ============================================================

detected_apneas = []

for start_time, end_time in merged_pauses:

    duration = (
        end_time
        - start_time
    )

    if duration >= APNEA_THRESHOLD:

        detected_apneas.append(
            (
                start_time,
                end_time
            )
        )


print()
print("======================================")
print("DETECTED APNEA EVENTS")
print("======================================")

print(
    "Detected pauses >= 10 sec:",
    len(merged_pauses)
)

print(
    "Detected apnea >= 20 sec:",
    len(detected_apneas)
)


# ============================================================
# LOAD REFERENCE ANNOTATIONS
#
# IMPORTANT:
# Your actual reference file is:
#
# infant1_resp.resp
#
# NOT .atr or .qrs
# ============================================================

print()
print("Loading PICSDB respiration annotations...")

annotations = wfdb.rdann(
    RECORD_PATH,
    "resp"
)

reference_samples = np.asarray(
    annotations.sample,
    dtype=np.int64
)

reference_times = (
    reference_samples
    / annotations.fs
)


print(
    "Reference annotations:",
    len(reference_times)
)

print(
    "Reference sampling frequency:",
    annotations.fs
)


# ============================================================
# CREATE REFERENCE APNEA EVENTS
# ============================================================

reference_intervals = (
    np.diff(reference_times)
)

reference_apneas = []

for i, interval in enumerate(
    reference_intervals
):

    if interval >= APNEA_THRESHOLD:

        reference_apneas.append(
            (
                reference_times[i],
                reference_times[i + 1]
            )
        )


print()
print("======================================")
print("REFERENCE APNEA EVENTS")
print("======================================")

print(
    "Reference apnea >= 20 sec:",
    len(reference_apneas)
)


# ============================================================
# EVENT MATCHING
# ============================================================

def event_distance(
    detected,
    reference
):

    detected_start, detected_end = detected
    reference_start, reference_end = reference

    start_difference = abs(
        detected_start
        - reference_start
    )

    end_difference = abs(
        detected_end
        - reference_end
    )

    # Use the smaller endpoint difference
    # as the primary matching measure.
    return min(
        start_difference,
        end_difference
    )


matched_reference = set()
matched_detected = set()

matches = []


# Build all possible pairs
possible_matches = []

for d_index, detected in enumerate(
    detected_apneas
):

    for r_index, reference in enumerate(
        reference_apneas
    ):

        distance = event_distance(
            detected,
            reference
        )

        if distance <= EVENT_MATCH_TOLERANCE:

            possible_matches.append(
                (
                    distance,
                    d_index,
                    r_index
                )
            )


# Closest matches first
possible_matches.sort(
    key=lambda x: x[0]
)


for distance, d_index, r_index in possible_matches:

    if d_index in matched_detected:
        continue

    if r_index in matched_reference:
        continue

    matched_detected.add(
        d_index
    )

    matched_reference.add(
        r_index
    )

    matches.append(
        (
            d_index,
            r_index,
            distance
        )
    )


true_positives = len(matches)

false_positives = (
    len(detected_apneas)
    - true_positives
)

false_negatives = (
    len(reference_apneas)
    - true_positives
)


# ============================================================
# METRICS
# ============================================================

if (
    true_positives
    + false_positives
) > 0:

    precision = (
        true_positives
        /
        (
            true_positives
            + false_positives
        )
    )

else:

    precision = 0.0


if (
    true_positives
    + false_negatives
) > 0:

    recall = (
        true_positives
        /
        (
            true_positives
            + false_negatives
        )
    )

else:

    recall = 0.0


if (
    precision
    + recall
) > 0:

    f1 = (
        2
        * precision
        * recall
        /
        (
            precision
            + recall
        )
    )

else:

    f1 = 0.0


# ============================================================
# RESULTS
# ============================================================

print()
print("======================================")
print("20+ SECOND APNEA EVALUATION")
print("======================================")

print(
    "Reference apnea events:",
    len(reference_apneas)
)

print(
    "Detected apnea events:",
    len(detected_apneas)
)

print(
    "True Positives:",
    true_positives
)

print(
    "False Positives:",
    false_positives
)

print(
    "False Negatives:",
    false_negatives
)

print(
    f"Precision: {precision:.3f}"
)

print(
    f"Recall:    {recall:.3f}"
)

print(
    f"F1-score:  {f1:.3f}"
)


# ============================================================
# SHOW MATCHED EVENTS
# ============================================================

print()
print("======================================")
print("MATCHED APNEA EVENTS")
print("======================================")


if matches:

    for number, (
        d_index,
        r_index,
        distance
    ) in enumerate(
        matches[:20],
        start=1
    ):

        detected_start, detected_end = (
            detected_apneas[d_index]
        )

        reference_start, reference_end = (
            reference_apneas[r_index]
        )

        print()
        print(
            f"{number}. "
            f"Detected: "
            f"{detected_start / 60:.2f} → "
            f"{detected_end / 60:.2f} min"
        )

        print(
            f"   Reference: "
            f"{reference_start / 60:.2f} → "
            f"{reference_end / 60:.2f} min"
        )

        print(
            f"   Timing difference: "
            f"{distance:.2f} sec"
        )

else:

    print(
        "No matched apnea events."
    )


# ============================================================
# FALSE POSITIVES
# ============================================================

print()
print("======================================")
print("FIRST FALSE POSITIVE EVENTS")
print("======================================")


fp_count = 0

for i, event in enumerate(
    detected_apneas
):

    if i not in matched_detected:

        start_time, end_time = event

        print(
            f"{fp_count + 1}. "
            f"{start_time / 60:.2f} → "
            f"{end_time / 60:.2f} min | "
            f"Duration: "
            f"{end_time - start_time:.2f} sec"
        )

        fp_count += 1

        if fp_count >= 20:
            break


# ============================================================
# FALSE NEGATIVES
# ============================================================

print()
print("======================================")
print("FIRST MISSED REFERENCE EVENTS")
print("======================================")


fn_count = 0

for i, event in enumerate(
    reference_apneas
):

    if i not in matched_reference:

        start_time, end_time = event

        print(
            f"{fn_count + 1}. "
            f"{start_time / 60:.2f} → "
            f"{end_time / 60:.2f} min | "
            f"Duration: "
            f"{end_time - start_time:.2f} sec"
        )

        fn_count += 1

        if fn_count >= 20:
            break


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("======================================")
print("FINAL SUMMARY")
print("======================================")

print(
    "Detected respiration peaks:",
    len(peaks)
)

print(
    "Reference apnea >= 20 sec:",
    len(reference_apneas)
)

print(
    "Detected apnea >= 20 sec:",
    len(detected_apneas)
)

print(
    f"Apnea Precision: {precision:.3f}"
)

print(
    f"Apnea Recall:    {recall:.3f}"
)

print(
    f"Apnea F1-score:  {f1:.3f}"
)

print()
print("Evaluation complete.")