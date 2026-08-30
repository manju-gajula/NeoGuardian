import wfdb
import numpy as np

# -----------------------------------------
# Settings
# -----------------------------------------

record_path = "data/picsdb/infant1_ecg"

fs = 250

BRADYCARDIA_HR = 100
MIN_DURATION = 1.2

# How close two events must be to count as a match
MATCH_TOLERANCE = 30  # seconds


# -----------------------------------------
# Load R-peaks
# -----------------------------------------

rpeaks = wfdb.rdann(record_path, "qrsc")
peak_samples = np.array(rpeaks.sample)


# -----------------------------------------
# Calculate heart rate
# -----------------------------------------

rr_intervals = np.diff(peak_samples) / fs

heart_rate = 60 / rr_intervals

hr_times = peak_samples[1:] / fs


# -----------------------------------------
# Detect bradycardia candidates
# -----------------------------------------

brady_mask = heart_rate < BRADYCARDIA_HR

detected_events = []

start = None

for i, is_brady in enumerate(brady_mask):

    if is_brady and start is None:
        start = i

    elif not is_brady and start is not None:

        end = i - 1

        duration = hr_times[end] - hr_times[start]

        if duration >= MIN_DURATION:

            detected_events.append(
                (
                    hr_times[start],
                    hr_times[end]
                )
            )

        start = None


# Handle event reaching the end
if start is not None:

    end = len(heart_rate) - 1

    duration = hr_times[end] - hr_times[start]

    if duration >= MIN_DURATION:

        detected_events.append(
            (
                hr_times[start],
                hr_times[end]
            )
        )


# -----------------------------------------
# Load PICSDB bradycardia annotations
# -----------------------------------------

annotations = wfdb.rdann(record_path, "atr")

reference_samples = np.array(annotations.sample)

reference_events = reference_samples / fs


# -----------------------------------------
# Match detected events with annotations
# -----------------------------------------

matched_reference = set()

true_positives = 0
false_positives = 0

matches = []


for detected_start, detected_end in detected_events:

    detected_center = (
        detected_start + detected_end
    ) / 2

    best_match = None
    best_distance = float("inf")

    for j, reference_time in enumerate(reference_events):

        if j in matched_reference:
            continue

        distance = abs(
            detected_center - reference_time
        )

        if distance < best_distance:

            best_distance = distance
            best_match = j

    if (
        best_match is not None
        and best_distance <= MATCH_TOLERANCE
    ):

        true_positives += 1

        matched_reference.add(best_match)

        matches.append(
            (
                detected_center,
                reference_events[best_match],
                best_distance
            )
        )

    else:

        false_positives += 1


# -----------------------------------------
# False negatives
# -----------------------------------------

false_negatives = (
    len(reference_events)
    - len(matched_reference)
)


# -----------------------------------------
# Metrics
# -----------------------------------------

if true_positives + false_positives > 0:

    precision = (
        true_positives
        / (true_positives + false_positives)
    )

else:

    precision = 0


if true_positives + false_negatives > 0:

    recall = (
        true_positives
        / (true_positives + false_negatives)
    )

else:

    recall = 0


if precision + recall > 0:

    f1 = (
        2 * precision * recall
        / (precision + recall)
    )

else:

    f1 = 0


# -----------------------------------------
# Results
# -----------------------------------------

print("\n======================================")
print("BRADYCARDIA DETECTOR EVALUATION")
print("======================================")

print(
    "\nReference PICSDB events:",
    len(reference_events)
)

print(
    "Detected candidate events:",
    len(detected_events)
)

print(
    "\nTrue Positives:",
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

print("\n--------------------------------------")

print(
    f"Precision: {precision:.3f}"
)

print(
    f"Recall:    {recall:.3f}"
)

print(
    f"F1-score:  {f1:.3f}"
)

print("--------------------------------------")


# -----------------------------------------
# Show matched events
# -----------------------------------------

print("\nFirst 20 matched events:")

for i, match in enumerate(matches[:20]):

    detected_time, reference_time, distance = match

    print(
        f"{i + 1}. "
        f"Detected: {detected_time / 60:.2f} min | "
        f"Reference: {reference_time / 60:.2f} min | "
        f"Difference: {distance:.2f} sec"
    )