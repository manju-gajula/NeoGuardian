import wfdb
import numpy as np
from scipy.signal import butter, sosfiltfilt, find_peaks


# ============================================================
# SETTINGS
# ============================================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

LOWCUT = 0.1
HIGHCUT = 0.8

MIN_BREATH_INTERVAL = 1.5
RESP_PROMINENCE = 0.60


# ============================================================
# LOAD REFERENCE RESPIRATION ANNOTATIONS
# ============================================================

print("Loading reference respiration annotations...")

annotations = wfdb.rdann(
    RECORD_PATH,
    "resp"
)

reference_peaks = (
    np.asarray(
        annotations.sample,
        dtype=int
    )
)

reference_times = (
    reference_peaks / annotations.fs
)

print("Reference annotations loaded!")
print(
    "Reference respiration peaks:",
    len(reference_peaks)
)

print(
    "Reference sampling frequency:",
    annotations.fs
)


# ============================================================
# LOAD RESPIRATION SIGNAL
# ============================================================

print("\nLoading respiration signal...")

header = wfdb.rdheader(
    RECORD_PATH
)

total_samples = header.sig_len

print(
    "Total samples:",
    total_samples
)

print(
    "Duration:",
    round(
        total_samples / FS / 60,
        2
    ),
    "minutes"
)


# ============================================================
# ANALYZE A REPRESENTATIVE 10-MINUTE WINDOW
# ============================================================

# We deliberately start around a known region containing
# respiratory activity rather than processing the entire
# 45+ hour record.

START_MINUTE = 210

WINDOW_SECONDS = 600

start_sample = (
    START_MINUTE
    * 60
    * FS
)

end_sample = min(
    start_sample
    + WINDOW_SECONDS * FS,
    total_samples
)

print("\n======================================")
print("DIAGNOSTIC WINDOW")
print("======================================")

print(
    "Start:",
    START_MINUTE,
    "minutes"
)

print(
    "End:",
    end_sample / FS / 60,
    "minutes"
)


# ============================================================
# LOAD SIGNAL WINDOW
# ============================================================

record = wfdb.rdrecord(
    RECORD_PATH,
    sampfrom=start_sample,
    sampto=end_sample,
    channels=[0]
)

signal = record.p_signal[:, 0]


# ============================================================
# BANDPASS FILTER
# ============================================================

nyquist = FS / 2

low = LOWCUT / nyquist
high = HIGHCUT / nyquist

sos = butter(
    4,
    [low, high],
    btype="band",
    output="sos"
)

filtered = sosfiltfilt(
    sos,
    signal
)

filtered -= np.mean(
    filtered
)

std = np.std(
    filtered
)

if std > 0:

    filtered /= std


# ============================================================
# DETECT RESPIRATION PEAKS
# ============================================================

min_distance = int(
    MIN_BREATH_INTERVAL * FS
)

detected_local, properties = find_peaks(
    filtered,
    distance=min_distance,
    prominence=RESP_PROMINENCE
)

detected_global = (
    detected_local
    + start_sample
)

detected_times = (
    detected_global / FS
)


print("\n======================================")
print("PEAK DETECTION")
print("======================================")

print(
    "Detected peaks:",
    len(detected_times)
)


# ============================================================
# GET REFERENCE PEAKS IN SAME WINDOW
# ============================================================

reference_in_window = (
    reference_times[
        (reference_times >= start_sample / FS)
        &
        (reference_times <= end_sample / FS)
    ]
)


print(
    "Reference peaks:",
    len(reference_in_window)
)


# ============================================================
# MATCH PEAKS
# ============================================================

MATCH_TOLERANCE = 2.0

matched_detected = set()
matched_reference = set()

matches = []

for di, detected in enumerate(
    detected_times
):

    differences = np.abs(
        reference_in_window
        - detected
    )

    if len(differences) == 0:
        continue

    ri = np.argmin(
        differences
    )

    difference = (
        differences[ri]
    )

    if difference <= MATCH_TOLERANCE:

        if di not in matched_detected:

            if ri not in matched_reference:

                matched_detected.add(
                    di
                )

                matched_reference.add(
                    ri
                )

                matches.append(
                    (
                        detected,
                        reference_in_window[ri],
                        difference
                    )
                )


true_positives = len(
    matches
)

false_positives = (
    len(detected_times)
    - true_positives
)

false_negatives = (
    len(reference_in_window)
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

    precision = 0


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

    recall = 0


if precision + recall > 0:

    f1 = (
        2
        * precision
        * recall
        /
        (precision + recall)
    )

else:

    f1 = 0


# ============================================================
# RESULTS
# ============================================================

print("\n======================================")
print("PEAK MATCHING RESULTS")
print("======================================")

print(
    "True positives:",
    true_positives
)

print(
    "False positives:",
    false_positives
)

print(
    "False negatives:",
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
# INTERVAL ANALYSIS
# ============================================================

detected_intervals = np.diff(
    detected_times
)

reference_intervals = np.diff(
    reference_in_window
)


print("\n======================================")
print("DETECTED RESPIRATION INTERVALS")
print("======================================")


if len(detected_intervals) > 0:

    print(
        "Minimum:",
        round(
            np.min(
                detected_intervals
            ),
            3
        ),
        "sec"
    )

    print(
        "Median:",
        round(
            np.median(
                detected_intervals
            ),
            3
        ),
        "sec"
    )

    print(
        "Maximum:",
        round(
            np.max(
                detected_intervals
            ),
            3
        ),
        "sec"
    )

    print(
        "10th percentile:",
        round(
            np.percentile(
                detected_intervals,
                10
            ),
            3
        ),
        "sec"
    )

    print(
        "90th percentile:",
        round(
            np.percentile(
                detected_intervals,
                90
            ),
            3
        ),
        "sec"
    )


print("\n======================================")
print("REFERENCE RESPIRATION INTERVALS")
print("======================================")


if len(reference_intervals) > 0:

    print(
        "Minimum:",
        round(
            np.min(
                reference_intervals
            ),
            3
        ),
        "sec"
    )

    print(
        "Median:",
        round(
            np.median(
                reference_intervals
            ),
            3
        ),
        "sec"
    )

    print(
        "Maximum:",
        round(
            np.max(
                reference_intervals
            ),
            3
        ),
        "sec"
    )

    print(
        "10th percentile:",
        round(
            np.percentile(
                reference_intervals,
                10
            ),
            3
        ),
        "sec"
    )

    print(
        "90th percentile:",
        round(
            np.percentile(
                reference_intervals,
                90
            ),
            3
        ),
        "sec"
    )


# ============================================================
# SHOW MATCHED PEAKS
# ============================================================

print("\n======================================")
print("FIRST 20 MATCHED PEAKS")
print("======================================")


for i, (
    detected,
    reference,
    difference
) in enumerate(
    matches[:20],
    start=1
):

    print(
        f"{i}. "
        f"Detected: {detected / 60:.3f} min | "
        f"Reference: {reference / 60:.3f} min | "
        f"Difference: {difference:.3f} sec"
    )


# ============================================================
# SHOW FALSE DETECTIONS
# ============================================================

print("\n======================================")
print("FIRST 20 FALSE DETECTED PEAKS")
print("======================================")


count = 0

for i, detected in enumerate(
    detected_times
):

    if i in matched_detected:
        continue

    print(
        f"{count + 1}. "
        f"{detected / 60:.3f} min"
    )

    count += 1

    if count >= 20:
        break


if count == 0:

    print(
        "No false detected peaks."
    )


# ============================================================
# SHOW MISSED REFERENCE PEAKS
# ============================================================

print("\n======================================")
print("FIRST 20 MISSED REFERENCE PEAKS")
print("======================================")


count = 0

for i, reference in enumerate(
    reference_in_window
):

    if i in matched_reference:
        continue

    print(
        f"{count + 1}. "
        f"{reference / 60:.3f} min"
    )

    count += 1

    if count >= 20:
        break


if count == 0:

    print(
        "No missed reference peaks."
    )


print("\n======================================")
print("DIAGNOSTIC COMPLETE")
print("======================================")