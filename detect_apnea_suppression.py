import wfdb
import numpy as np
from scipy.signal import butter, sosfiltfilt


# ============================================================
# SETTINGS
# ============================================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

# Minimum duration for an apnea event
APNEA_THRESHOLD = 20.0

# Analyze signal in chunks
CHUNK_SECONDS = 600

# Window used to calculate local respiration amplitude
BASELINE_WINDOW = 10.0

# Suppression threshold
#
# ratio = during_amplitude / before_amplitude
#
# Lower ratio = stronger suppression.
#
# Start conservatively.
SUPPRESSION_THRESHOLD = 0.50

# Minimum signal amplitude to avoid detecting
# events in almost-flat/noisy regions
MIN_BASELINE_AMPLITUDE = 0.001

# Merge nearby suppression regions
MERGE_GAP = 5.0


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
# AMPLITUDE ENVELOPE
# ============================================================

print()
print("Calculating respiration amplitude envelope...")

# Use absolute value of filtered respiration.
#
# This gives us an estimate of how much respiratory
# activity is present at each point.

absolute_signal = np.abs(
    filtered
)

# Smooth over approximately 2 seconds.
smooth_samples = int(
    2.0 * FS
)

kernel = np.ones(
    smooth_samples
) / smooth_samples

amplitude = np.convolve(
    absolute_signal,
    kernel,
    mode="same"
)


# ============================================================
# NORMALIZE LOCALLY
# ============================================================

print()
print("Analyzing respiratory suppression...")


def local_median(
    data,
    center,
    half_window
):

    start = max(
        0,
        center - half_window
    )

    end = min(
        len(data),
        center + half_window
    )

    if end <= start:
        return 0.0

    return np.median(
        data[start:end]
    )


# ============================================================
# DETECT SUPPRESSION
# ============================================================

candidate_events = []

step_seconds = 2.0

step_samples = int(
    step_seconds * FS
)

baseline_samples = int(
    BASELINE_WINDOW * FS
)

half_baseline = (
    baseline_samples // 2
)

minimum_samples = int(
    APNEA_THRESHOLD * FS
)


# We examine the signal every 2 seconds.
for center in range(
    half_baseline,
    total_samples - half_baseline,
    step_samples
):

    current_amplitude = amplitude[
        max(
            0,
            center - step_samples // 2
        ):
        min(
            total_samples,
            center + step_samples // 2
        )
    ]

    if len(current_amplitude) == 0:
        continue

    during_amplitude = np.median(
        current_amplitude
    )

    before_start = max(
        0,
        center - baseline_samples
    )

    before_end = center

    before_amplitude = np.median(
        amplitude[
            before_start:before_end
        ]
    )

    after_start = center

    after_end = min(
        total_samples,
        center + baseline_samples
    )

    after_amplitude = np.median(
        amplitude[
            after_start:after_end
        ]
    )

    if (
        before_amplitude
        < MIN_BASELINE_AMPLITUDE
    ):
        continue

    suppression_ratio = (
        during_amplitude
        /
        before_amplitude
    )

    # --------------------------------------------------------
    # Strong suppression
    # --------------------------------------------------------

    if (
        suppression_ratio
        <= SUPPRESSION_THRESHOLD
    ):

        start_time = (
            center / FS
        )

        candidate_events.append(
            (
                start_time,
                suppression_ratio,
                before_amplitude,
                during_amplitude,
                after_amplitude
            )
        )


# ============================================================
# CONVERT POINTS INTO CONTINUOUS EVENTS
# ============================================================

print()
print("Grouping suppression regions...")


suppression_regions = []

if candidate_events:

    region_start = (
        candidate_events[0][0]
    )

    region_end = (
        candidate_events[0][0]
        + step_seconds
    )

    region_values = [
        candidate_events[0]
    ]

    for event in candidate_events[1:]:

        event_time = event[0]

        if (
            event_time
            - region_end
            <= MERGE_GAP
        ):

            region_end = (
                event_time
                + step_seconds
            )

            region_values.append(
                event
            )

        else:

            suppression_regions.append(
                (
                    region_start,
                    region_end,
                    region_values
                )
            )

            region_start = event_time

            region_end = (
                event_time
                + step_seconds
            )

            region_values = [
                event
            ]

    suppression_regions.append(
        (
            region_start,
            region_end,
            region_values
        )
    )


# ============================================================
# FILTER BY DURATION
# ============================================================

apnea_events = []

for (
    start_time,
    end_time,
    values
) in suppression_regions:

    duration = (
        end_time
        - start_time
    )

    if duration < APNEA_THRESHOLD:
        continue

    ratios = [
        item[1]
        for item in values
    ]

    before_values = [
        item[2]
        for item in values
    ]

    during_values = [
        item[3]
        for item in values
    ]

    after_values = [
        item[4]
        for item in values
    ]

    apnea_events.append(
        {
            "start": start_time,
            "end": end_time,
            "duration": duration,
            "suppression_ratio": np.median(
                ratios
            ),
            "before_amplitude": np.median(
                before_values
            ),
            "during_amplitude": np.median(
                during_values
            ),
            "after_amplitude": np.median(
                after_values
            )
        }
    )


# ============================================================
# LOAD REFERENCE EVENTS
# ============================================================

print()
print(
    "Loading reference respiration annotations..."
)

annotations = wfdb.rdann(
    RECORD_PATH,
    "resp"
)

reference_times = (
    np.asarray(
        annotations.sample,
        dtype=np.float64
    )
    / annotations.fs
)

reference_intervals = np.diff(
    reference_times
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


# ============================================================
# OUTPUT DETECTED EVENTS
# ============================================================

print()
print("======================================")
print("SUPPRESSION-BASED APNEA DETECTION")
print("======================================")

print(
    "Suppression threshold:",
    SUPPRESSION_THRESHOLD
)

print(
    "Apnea threshold:",
    APNEA_THRESHOLD,
    "seconds"
)

print(
    "Reference apnea events:",
    len(reference_apneas)
)

print(
    "Detected apnea events:",
    len(apnea_events)
)


if apnea_events:

    print()
    print(
        "Detected apnea events:"
    )

    for i, event in enumerate(
        apnea_events,
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
            f"Before amplitude: "
            f"{event['before_amplitude']:.6f}"
        )

        print(
            f"During amplitude: "
            f"{event['during_amplitude']:.6f}"
        )

        print(
            f"After amplitude: "
            f"{event['after_amplitude']:.6f}"
        )

else:

    print(
        "No suppression-based apnea events found."
    )


# ============================================================
# SIMPLE EVENT MATCHING
# ============================================================

MATCH_TOLERANCE = 15.0

matched_reference = set()
matched_detected = set()

matches = []

for d_index, detected in enumerate(
    apnea_events
):

    best_reference = None
    best_distance = None

    for r_index, reference in enumerate(
        reference_apneas
    ):

        if r_index in matched_reference:
            continue

        detected_start = (
            detected["start"]
        )

        detected_end = (
            detected["end"]
        )

        reference_start = (
            reference[0]
        )

        reference_end = (
            reference[1]
        )

        start_diff = abs(
            detected_start
            - reference_start
        )

        end_diff = abs(
            detected_end
            - reference_end
        )

        distance = (
            start_diff
            + end_diff
        )

        if distance <= MATCH_TOLERANCE:

            if (
                best_distance is None
                or distance < best_distance
            ):

                best_distance = distance
                best_reference = r_index

    if best_reference is not None:

        matched_detected.add(
            d_index
        )

        matched_reference.add(
            best_reference
        )

        matches.append(
            (
                d_index,
                best_reference,
                best_distance
            )
        )


# ============================================================
# METRICS
# ============================================================

true_positives = len(
    matches
)

false_positives = (
    len(apnea_events)
    - true_positives
)

false_negatives = (
    len(reference_apneas)
    - true_positives
)

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
# FINAL EVALUATION
# ============================================================

print()
print("======================================")
print("SUPPRESSION DETECTOR EVALUATION")
print("======================================")

print(
    "Reference apnea events:",
    len(reference_apneas)
)

print(
    "Detected apnea events:",
    len(apnea_events)
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
# MATCHED EVENTS
# ============================================================

print()
print("======================================")
print("MATCHED EVENTS")
print("======================================")


for number, (
    d_index,
    r_index,
    distance
) in enumerate(
    matches,
    start=1
):

    detected = apnea_events[
        d_index
    ]

    reference = reference_apneas[
        r_index
    ]

    print()
    print(
        f"Match {number}"
    )

    print(
        f"Detected: "
        f"{detected['start'] / 60:.2f} → "
        f"{detected['end'] / 60:.2f} min"
    )

    print(
        f"Reference: "
        f"{reference[0] / 60:.2f} → "
        f"{reference[1] / 60:.2f} min"
    )

    print(
        f"Suppression ratio: "
        f"{detected['suppression_ratio']:.3f}"
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("======================================")
print("FINAL SUMMARY")
print("======================================")

print(
    "Reference apnea events:",
    len(reference_apneas)
)

print(
    "Detected suppression-based apnea events:",
    len(apnea_events)
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

print()
print("Analysis complete.")