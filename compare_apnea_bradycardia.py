import wfdb
import numpy as np
import os


# ============================================================
# SETTINGS
# ============================================================

RESP_RECORD = "data/picsdb/infant1_resp"
ECG_RECORD = "data/picsdb/infant1_ecg"

# Your detected apnea events are written in MINUTES.
# This script converts them to seconds before comparison.

DETECTED_EVENTS = [
    (218.23, 218.67),
    (498.06, 498.71),
    (588.83, 589.31),
    (759.21, 759.62),
    (953.19, 953.53),
    (1069.11, 1069.47),
    (1720.80, 1721.56),
    (1953.91, 1954.25),
    (1955.90, 1956.29),
    (1956.42, 1956.82),
    (1958.60, 1958.96),
    (2140.51, 2140.91),
    (2551.22, 2551.68),
]

# ============================================================
# IMPORTANT
# ============================================================
# If your latest detector produced 23 events rather than the
# 13-event list above, replace the list above with ALL 23
# detected events, still written in MINUTES.
#
# The matching code below automatically converts minutes -> sec.


APNEA_THRESHOLD = 20.0

BRADYCARDIA_THRESHOLD = 100.0

POSSIBLE_BRADY_FRACTION = 0.10

STRONG_BRADY_FRACTION = 0.50

BEFORE_WINDOW = 30.0

AFTER_WINDOW = 30.0

# Maximum center-time difference allowed for matching.
MATCH_TOLERANCE = 30.0


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_mean(values):

    if len(values) == 0:
        return None

    return float(np.mean(values))


def safe_min(values):

    if len(values) == 0:
        return None

    return float(np.min(values))


def format_value(value, digits=1):

    if value is None:
        return "NA"

    return f"{value:.{digits}f}"


def classify_bradycardia(
    brady_fraction,
    available
):

    if not available:
        return "HR UNAVAILABLE"

    if brady_fraction >= STRONG_BRADY_FRACTION:
        return "STRONG BRADYCARDIA"

    if brady_fraction >= POSSIBLE_BRADY_FRACTION:
        return "POSSIBLE BRADYCARDIA"

    return "NO BRADYCARDIA"


def event_center(event):

    return (
        event[0] + event[1]
    ) / 2.0


# ============================================================
# LOAD RESPIRATION ANNOTATIONS
# ============================================================

print("======================================")
print("LOADING REFERENCE RESPIRATION")
print("======================================")

resp_record = wfdb.rdrecord(
    RESP_RECORD,
    physical=False
)

resp_fs = float(
    resp_record.fs
)

try:

    resp_ann = wfdb.rdann(
        RESP_RECORD,
        "resp"
    )

except Exception as e:

    print()
    print("ERROR loading respiration annotations.")
    print(e)
    raise SystemExit


print(
    "Reference respiration annotations:",
    len(resp_ann.sample)
)

print(
    "Reference respiration FS:",
    resp_fs
)


# ============================================================
# EXTRACT REFERENCE APNEA EVENTS
# ============================================================

print()
print("======================================")
print("REFERENCE APNEA EVENTS")
print("======================================")


# ------------------------------------------------------------
# IMPORTANT:
# The respiration annotation file uses sample positions.
#
# We identify long intervals between respiratory annotations.
# ------------------------------------------------------------

resp_times = (
    np.asarray(
        resp_ann.sample,
        dtype=np.float64
    )
    / resp_fs
)

resp_times = np.sort(
    resp_times
)

resp_intervals = np.diff(
    resp_times
)

reference_events = []

for i, interval in enumerate(
    resp_intervals
):

    if interval >= APNEA_THRESHOLD:

        start = resp_times[i]

        end = resp_times[i + 1]

        reference_events.append(
            (
                float(start),
                float(end)
            )
        )


print(
    "Reference apnea events:",
    len(reference_events)
)


# ============================================================
# LOAD ECG R-PEAK ANNOTATIONS
# ============================================================

print()
print("======================================")
print("LOADING ECG R-PEAKS")
print("======================================")


ECG_ANNOTATION = "qrsc"

try:

    ecg_record = wfdb.rdrecord(
        ECG_RECORD,
        physical=False
    )

    ecg_fs = float(
        ecg_record.fs
    )

except Exception as e:

    print()
    print("ERROR loading ECG record.")
    print(e)
    raise SystemExit


try:

    ecg_ann = wfdb.rdann(
        ECG_RECORD,
        ECG_ANNOTATION
    )

except Exception as e:

    print()
    print("ERROR loading ECG annotations.")
    print()
    print(
        "Expected annotation:"
    )
    print(
        f"{ECG_RECORD}.{ECG_ANNOTATION}"
    )
    print()
    print(e)

    raise SystemExit


print(
    "ECG annotation:",
    ECG_ANNOTATION
)

print(
    "ECG sampling frequency:",
    ecg_fs
)

print(
    "Total R-peaks:",
    len(ecg_ann.sample)
)


# ============================================================
# CONVERT ECG R-PEAKS TO SECONDS
# ============================================================

rpeak_times = (
    np.asarray(
        ecg_ann.sample,
        dtype=np.float64
    )
    / ecg_fs
)

rpeak_times = np.sort(
    rpeak_times
)


# ============================================================
# HEART RATE CALCULATION
# ============================================================

def get_hr_for_window(
    start_time,
    end_time
):

    indices = np.where(
        (
            rpeak_times >= start_time
        )
        &
        (
            rpeak_times <= end_time
        )
    )[0]

    if len(indices) < 2:

        return np.array(
            [],
            dtype=np.float64
        )

    selected_peaks = (
        rpeak_times[indices]
    )

    rr = np.diff(
        selected_peaks
    )

    # Remove impossible RR intervals.
    valid_rr = (
        (rr >= 0.25)
        &
        (rr <= 2.0)
    )

    rr = rr[
        valid_rr
    ]

    if len(rr) == 0:

        return np.array(
            [],
            dtype=np.float64
        )

    hr = (
        60.0 / rr
    )

    # Remove implausible HR values.
    hr = hr[
        (hr >= 30.0)
        &
        (hr <= 240.0)
    ]

    return hr


# ============================================================
# ANALYZE REFERENCE APNEA + BRADYCARDIA
# ============================================================

print()
print("======================================")
print("REFERENCE APNEA + BRADYCARDIA")
print("======================================")


reference_results = []

strong_brady_count = 0

possible_brady_count = 0

any_brady_count = 0


for event_number, (
    start,
    end
) in enumerate(
    reference_events,
    start=1
):

    before_start = max(
        0.0,
        start - BEFORE_WINDOW
    )

    before_end = start

    after_start = end

    after_end = (
        end + AFTER_WINDOW
    )

    before_hr = get_hr_for_window(
        before_start,
        before_end
    )

    during_hr = get_hr_for_window(
        start,
        end
    )

    after_hr = get_hr_for_window(
        after_start,
        after_end
    )

    if len(before_hr) > 0:

        mean_before = safe_mean(
            before_hr
        )

    else:

        mean_before = None


    if len(during_hr) > 0:

        mean_during = safe_mean(
            during_hr
        )

        min_during = safe_min(
            during_hr
        )

        below_100 = int(
            np.sum(
                during_hr
                < BRADYCARDIA_THRESHOLD
            )
        )

        brady_fraction = (
            below_100
            / len(during_hr)
        )

        available = True

    else:

        mean_during = None

        min_during = None

        below_100 = 0

        brady_fraction = 0.0

        available = False


    if len(after_hr) > 0:

        mean_after = safe_mean(
            after_hr
        )

    else:

        mean_after = None


    classification = classify_bradycardia(
        brady_fraction,
        available
    )


    if available:

        if below_100 > 0:

            any_brady_count += 1

        if (
            brady_fraction
            >= POSSIBLE_BRADY_FRACTION
        ):

            possible_brady_count += 1

        if (
            brady_fraction
            >= STRONG_BRADY_FRACTION
        ):

            strong_brady_count += 1


    reference_results.append(
        {
            "start": start,
            "end": end,
            "duration": end - start,
            "before_hr": mean_before,
            "during_hr": mean_during,
            "min_hr": min_during,
            "after_hr": mean_after,
            "below_100": below_100,
            "brady_fraction":
                brady_fraction,
            "classification":
                classification
        }
    )


# ============================================================
# PRINT REFERENCE RESULTS
# ============================================================

for i, result in enumerate(
    reference_results,
    start=1
):

    print()

    print(
        f"Event {i}/{len(reference_results)}"
    )

    print(
        f"Time: "
        f"{result['start'] / 60:.2f} "
        f"-> "
        f"{result['end'] / 60:.2f} min"
    )

    print(
        f"Duration: "
        f"{result['duration']:.2f} sec"
    )

    print(
        f"Before HR: "
        f"{format_value(result['before_hr'])} BPM"
    )

    print(
        f"During HR: "
        f"{format_value(result['during_hr'])} BPM"
    )

    print(
        f"Minimum HR: "
        f"{format_value(result['min_hr'])} BPM"
    )

    print(
        f"After HR: "
        f"{format_value(result['after_hr'])} BPM"
    )

    print(
        f"HR values < 100 BPM: "
        f"{result['below_100']}"
    )

    print(
        f"Bradycardia fraction: "
        f"{result['brady_fraction']:.3f}"
    )

    print(
        f"Classification: "
        f"{result['classification']}"
    )


# ============================================================
# CONVERT DETECTED EVENTS
# ============================================================

print()
print("======================================")
print("DETECTED APNEA EVENTS")
print("======================================")


# Convert detector output from MINUTES to SECONDS.

detected_events = []

for start_min, end_min in DETECTED_EVENTS:

    start_sec = (
        start_min * 60.0
    )

    end_sec = (
        end_min * 60.0
    )

    if (
        end_sec - start_sec
        >= APNEA_THRESHOLD
    ):

        detected_events.append(
            (
                start_sec,
                end_sec
            )
        )


print(
    "Detected apnea events:",
    len(detected_events)
)


# ============================================================
# MATCH DETECTED TO REFERENCE
# ============================================================

print()
print("======================================")
print("MATCHED DETECTED / REFERENCE APNEA")
print("======================================")


matched_pairs = []

used_reference = set()

used_detected = set()


# ------------------------------------------------------------
# Match by closest event center.
# This avoids the previous minutes-vs-seconds bug.
# ------------------------------------------------------------

for d_index, detected in enumerate(
    detected_events
):

    d_center = event_center(
        detected
    )

    best_index = None

    best_difference = None

    for r_index, reference in enumerate(
        reference_events
    ):

        if r_index in used_reference:
            continue

        r_center = event_center(
            reference
        )

        difference = abs(
            d_center - r_center
        )

        if (
            best_difference is None
            or difference < best_difference
        ):

            best_difference = difference

            best_index = r_index


    if (
        best_index is not None
        and best_difference
        <= MATCH_TOLERANCE
    ):

        matched_pairs.append(
            (
                d_index,
                best_index,
                best_difference
            )
        )

        used_detected.add(
            d_index
        )

        used_reference.add(
            best_index
        )


print(
    "Matched apnea events:",
    len(matched_pairs)
)


for number, (
    d_index,
    r_index,
    difference
) in enumerate(
    matched_pairs,
    start=1
):

    detected = detected_events[
        d_index
    ]

    reference = reference_events[
        r_index
    ]

    print()

    print(
        f"{number}. "
        f"Detected: "
        f"{detected[0] / 60:.2f}"
        f" -> "
        f"{detected[1] / 60:.2f} min"
    )

    print(
        f"   Reference: "
        f"{reference[0] / 60:.2f}"
        f" -> "
        f"{reference[1] / 60:.2f} min"
    )

    print(
        f"   Center difference: "
        f"{difference:.2f} sec"
    )


# ============================================================
# APNEA PERFORMANCE
# ============================================================

true_positives = len(
    matched_pairs
)

false_positives = (
    len(detected_events)
    - true_positives
)

false_negatives = (
    len(reference_events)
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
    precision + recall
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
# CARDIORESPIRATORY EVENTS
# ============================================================

print()
print("======================================")
print("CARDIORESPIRATORY EVENTS")
print("======================================")


cardiorespiratory_events = []

strong_cardiorespiratory = []

possible_cardiorespiratory = []


for (
    d_index,
    r_index,
    difference
) in matched_pairs:

    reference = reference_results[
        r_index
    ]

    classification = (
        reference["classification"]
    )

    if classification == (
        "STRONG BRADYCARDIA"
    ):

        strong_cardiorespiratory.append(
            (
                d_index,
                r_index
            )
        )

        cardiorespiratory_events.append(
            (
                d_index,
                r_index
            )
        )

    elif classification == (
        "POSSIBLE BRADYCARDIA"
    ):

        possible_cardiorespiratory.append(
            (
                d_index,
                r_index
            )
        )

        cardiorespiratory_events.append(
            (
                d_index,
                r_index
            )
        )


print(
    "Detected apnea + strong bradycardia:",
    len(strong_cardiorespiratory)
)

print(
    "Detected apnea + possible bradycardia:",
    len(possible_cardiorespiratory)
)

print(
    "Detected apnea + any bradycardia:",
    len(cardiorespiratory_events)
)


# ============================================================
# CARDIORESPIRATORY EVENT LIST
# ============================================================

print()
print("======================================")
print("CARDIORESPIRATORY EVENT LIST")
print("======================================")


for number, (
    d_index,
    r_index
) in enumerate(
    cardiorespiratory_events,
    start=1
):

    detected = detected_events[
        d_index
    ]

    reference = reference_events[
        r_index
    ]

    result = reference_results[
        r_index
    ]

    print()

    print(
        f"Event {number}"
    )

    print(
        f"Detected apnea: "
        f"{detected[0] / 60:.2f}"
        f" -> "
        f"{detected[1] / 60:.2f} min"
    )

    print(
        f"Reference apnea: "
        f"{reference[0] / 60:.2f}"
        f" -> "
        f"{reference[1] / 60:.2f} min"
    )

    print(
        f"Mean HR: "
        f"{format_value(result['during_hr'])} BPM"
    )

    print(
        f"Minimum HR: "
        f"{format_value(result['min_hr'])} BPM"
    )

    print(
        f"HR <100: "
        f"{result['below_100']}"
    )

    print(
        f"Bradycardia: "
        f"{result['classification']}"
    )


# ============================================================
# REFERENCE TABLE
# ============================================================

print()
print("======================================")
print("REFERENCE APNEA / BRADYCARDIA TABLE")
print("======================================")


print(
    "Event | Start | End | Duration | "
    "Mean HR | Min HR | <100 | Brady | Detected"
)

print(
    "-" * 100
)


matched_reference_indices = {
    r_index
    for (
        _,
        r_index,
        _
    )
    in matched_pairs
}


for i, result in enumerate(
    reference_results,
    start=1
):

    detected_status = (
        "YES"
        if (i - 1)
        in used_reference
        else "NO"
    )

    print(
        f"{i:5d} | "
        f"{result['start'] / 60:7.2f} | "
        f"{result['end'] / 60:7.2f} | "
        f"{result['duration']:8.2f} | "
        f"{format_value(result['during_hr'], 1):>7} | "
        f"{format_value(result['min_hr'], 1):>7} | "
        f"{result['below_100']:4d} | "
        f"{result['classification']:<18} | "
        f"{detected_status}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("======================================")
print("APNEA DETECTION PERFORMANCE")
print("======================================")

print(
    "Reference apnea events:",
    len(reference_events)
)

print(
    "Detected apnea events:",
    len(detected_events)
)

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


print()
print("======================================")
print("BRADYCARDIA RESULTS")
print("======================================")


print(
    "Reference apnea events:",
    len(reference_events)
)

print(
    "Events with HR < 100 BPM:",
    any_brady_count
)

print(
    "Possible bradycardia events:",
    possible_brady_count
)

print(
    "Strong bradycardia events:",
    strong_brady_count
)


print()
print("======================================")
print("CARDIORESPIRATORY RESULTS")
print("======================================")


print(
    "Cardiorespiratory events:",
    len(cardiorespiratory_events)
)

print(
    "Strong cardiorespiratory events:",
    len(strong_cardiorespiratory)
)

print(
    "Possible cardiorespiratory events:",
    len(possible_cardiorespiratory)
)


print()
print("======================================")
print("FINAL SUMMARY")
print("======================================")


print(
    "Reference apnea events:",
    len(reference_events)
)

print(
    "Detected apnea events:",
    len(detected_events)
)

print(
    f"Apnea precision: {precision:.3f}"
)

print(
    f"Apnea recall:    {recall:.3f}"
)

print(
    f"Apnea F1:        {f1:.3f}"
)

print()

print(
    "Events with any HR < 100 BPM:",
    any_brady_count
)

print(
    "Possible bradycardia:",
    possible_brady_count
)

print(
    "Strong bradycardia:",
    strong_brady_count
)

print(
    "Cardiorespiratory events:",
    len(cardiorespiratory_events)
)

print(
    "Strong cardiorespiratory events:",
    len(strong_cardiorespiratory)
)

print(
    "Possible cardiorespiratory events:",
    len(possible_cardiorespiratory)
)

print()
print(
    "Combined apnea + bradycardia analysis complete."
)