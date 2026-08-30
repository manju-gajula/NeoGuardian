import wfdb
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

RESP_RECORD = "data/picsdb/infant1_resp"
ECG_RECORD = "data/picsdb/infant1_ecg"

RESP_ANNOTATION = "resp"

# IMPORTANT:
# The ECG annotation in PICSDB is qrsc, NOT qrs.
ECG_ANNOTATION = "qrsc"

RESP_FS = 500.0

# Bradycardia threshold used for this analysis
BRADYCARDIA_THRESHOLD = 100.0

# Windows around each apnea event
BEFORE_WINDOW = 30.0
AFTER_WINDOW = 30.0


# ============================================================
# LOAD RESPIRATION ANNOTATIONS
# ============================================================

print()
print("======================================")
print("LOADING RESPIRATION ANNOTATIONS")
print("======================================")

print("Record:", RESP_RECORD)

resp_ann = wfdb.rdann(
    RESP_RECORD,
    RESP_ANNOTATION
)

print(
    "Total respiration annotations:",
    len(resp_ann.sample)
)

print(
    "Respiration annotation FS:",
    resp_ann.fs
)


# ============================================================
# EXTRACT REFERENCE APNEA EVENTS
# ============================================================

print()
print("======================================")
print("EXTRACTING REFERENCE APNEA EVENTS")
print("======================================")

resp_samples = np.asarray(
    resp_ann.sample,
    dtype=np.int64
)

# Convert annotation samples to seconds
resp_times = (
    resp_samples / float(resp_ann.fs)
)

# Respiratory annotation intervals
resp_intervals = np.diff(
    resp_times
)

reference_apnea_events = []

for i, interval in enumerate(
    resp_intervals
):

    if interval >= 20.0:

        start_time = resp_times[i]
        end_time = resp_times[i + 1]

        reference_apnea_events.append(
            (
                float(start_time),
                float(end_time)
            )
        )


print(
    "Reference apnea events:",
    len(reference_apnea_events)
)


if len(reference_apnea_events) == 0:

    print(
        "ERROR: No reference apnea events found."
    )

    raise SystemExit


# ============================================================
# LOAD ECG R-PEAK ANNOTATIONS
# ============================================================

print()
print("======================================")
print("LOADING ECG R-PEAK ANNOTATIONS")
print("======================================")

print("Record:", ECG_RECORD)
print("Annotation:", ECG_ANNOTATION)

try:

    ecg_ann = wfdb.rdann(
        ECG_RECORD,
        ECG_ANNOTATION
    )

except Exception as e:

    print()
    print("ERROR loading ECG annotations.")
    print()
    print("Expected annotation:")
    print(
        ECG_RECORD
        + "."
        + ECG_ANNOTATION
    )

    print()
    print("Actual error:")
    print(e)

    raise SystemExit


# ============================================================
# IMPORTANT: USE ACTUAL ECG ANNOTATION FS
# ============================================================

ECG_FS = float(
    ecg_ann.fs
)

print()
print(
    "Actual ECG annotation sampling frequency:",
    ECG_FS
)

rpeaks = np.asarray(
    ecg_ann.sample,
    dtype=np.int64
)

print(
    "Total R-peaks:",
    len(rpeaks)
)

if len(rpeaks) < 2:

    print(
        "ERROR: Not enough ECG R-peaks."
    )

    raise SystemExit


# ============================================================
# CONVERT R-PEAKS TO SECONDS
# ============================================================

rpeak_times = (
    rpeaks / ECG_FS
)

rpeak_times = np.asarray(
    rpeak_times,
    dtype=np.float64
)

print(
    "First R-peak time:",
    round(float(rpeak_times[0]), 3),
    "sec"
)

print(
    "Last R-peak time:",
    round(float(rpeak_times[-1]), 3),
    "sec"
)


# ============================================================
# HEART RATE CALCULATION
# ============================================================

def calculate_hr_values(
    start_time,
    end_time
):

    mask = (
        (rpeak_times >= start_time)
        &
        (rpeak_times <= end_time)
    )

    event_peaks = rpeak_times[
        mask
    ]

    if len(event_peaks) < 2:

        return np.array(
            [],
            dtype=np.float64
        )

    rr = np.diff(
        event_peaks
    )

    # Remove impossible RR intervals
    rr = rr[
        (rr >= 0.20)
        &
        (rr <= 2.00)
    ]

    if len(rr) == 0:

        return np.array(
            [],
            dtype=np.float64
        )

    hr = (
        60.0 / rr
    )

    # Remove physiologically implausible
    # calculated HR values
    hr = hr[
        (hr >= 30.0)
        &
        (hr <= 250.0)
    ]

    return hr


# ============================================================
# STATISTICS HELPER
# ============================================================

def mean_or_nan(values):

    if len(values) == 0:
        return np.nan

    return float(
        np.mean(values)
    )


def minimum_or_nan(values):

    if len(values) == 0:
        return np.nan

    return float(
        np.min(values)
    )


def count_below_threshold(values):

    if len(values) == 0:
        return 0

    return int(
        np.sum(
            values < BRADYCARDIA_THRESHOLD
        )
    )


# ============================================================
# ANALYZE EACH APNEA EVENT
# ============================================================

print()
print("======================================")
print("APNEA / BRADYCARDIA ANALYSIS")
print("======================================")

print(
    "Bradycardia threshold:",
    BRADYCARDIA_THRESHOLD,
    "BPM"
)

print(
    "Before window:",
    BEFORE_WINDOW,
    "sec"
)

print(
    "After window:",
    AFTER_WINDOW,
    "sec"
)

results = []


for event_number, (
    apnea_start,
    apnea_end
) in enumerate(
    reference_apnea_events,
    start=1
):

    duration = (
        apnea_end
        - apnea_start
    )

    # --------------------------------------------------------
    # Before apnea
    # --------------------------------------------------------

    before_start = max(
        0.0,
        apnea_start
        - BEFORE_WINDOW
    )

    before_end = apnea_start

    before_hr = calculate_hr_values(
        before_start,
        before_end
    )

    # --------------------------------------------------------
    # During apnea
    # --------------------------------------------------------

    during_hr = calculate_hr_values(
        apnea_start,
        apnea_end
    )

    # --------------------------------------------------------
    # After apnea
    # --------------------------------------------------------

    after_start = apnea_end

    after_end = (
        apnea_end
        + AFTER_WINDOW
    )

    after_hr = calculate_hr_values(
        after_start,
        after_end
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    before_mean = mean_or_nan(
        before_hr
    )

    during_mean = mean_or_nan(
        during_hr
    )

    during_min = minimum_or_nan(
        during_hr
    )

    after_mean = mean_or_nan(
        after_hr
    )

    below_100 = count_below_threshold(
        during_hr
    )

    if len(during_hr) > 0:

        brady_fraction = (
            below_100
            / len(during_hr)
        )

    else:

        brady_fraction = 0.0

    # --------------------------------------------------------
    # Classification
    #
    # STRONG BRADYCARDIA:
    # At least 50% of valid HR measurements
    # during apnea are below 100 BPM.
    # --------------------------------------------------------

    if (
        len(during_hr) > 0
        and brady_fraction >= 0.50
    ):

        classification = (
            "STRONG BRADYCARDIA"
        )

    elif (
        len(during_hr) > 0
        and below_100 > 0
    ):

        classification = (
            "POSSIBLE BRADYCARDIA"
        )

    else:

        classification = (
            "NO BRADYCARDIA"
        )

    result = {

        "event": event_number,

        "start": apnea_start,

        "end": apnea_end,

        "duration": duration,

        "before_hr": before_mean,

        "during_hr": during_mean,

        "min_hr": during_min,

        "after_hr": after_mean,

        "below_100": below_100,

        "total_hr": len(during_hr),

        "brady_fraction":
            brady_fraction,

        "classification":
            classification
    }

    results.append(
        result
    )

    # --------------------------------------------------------
    # Print event
    # --------------------------------------------------------

    print()
    print(
        f"Event {event_number}/"
        f"{len(reference_apnea_events)}"
    )

    print(
        f"Time: "
        f"{apnea_start / 60:.2f} "
        f"-> "
        f"{apnea_end / 60:.2f} min"
    )

    print(
        f"Duration: "
        f"{duration:.2f} sec"
    )

    if np.isnan(before_mean):

        print(
            "Before HR: unavailable"
        )

    else:

        print(
            f"Before HR: "
            f"{before_mean:.2f} BPM"
        )

    if np.isnan(during_mean):

        print(
            "During HR: unavailable"
        )

    else:

        print(
            f"During HR: "
            f"{during_mean:.2f} BPM"
        )

    if np.isnan(during_min):

        print(
            "Minimum HR: unavailable"
        )

    else:

        print(
            f"Minimum HR: "
            f"{during_min:.2f} BPM"
        )

    if np.isnan(after_mean):

        print(
            "After HR: unavailable"
        )

    else:

        print(
            f"After HR: "
            f"{after_mean:.2f} BPM"
        )

    print(
        f"HR values < "
        f"{BRADYCARDIA_THRESHOLD:.0f} BPM: "
        f"{below_100}/"
        f"{len(during_hr)}"
    )

    print(
        f"Bradycardia fraction: "
        f"{brady_fraction:.3f}"
    )

    print(
        f"Classification: "
        f"{classification}"
    )


# ============================================================
# OVERALL RESULTS
# ============================================================

print()
print("======================================")
print("OVERALL BRADYCARDIA ANALYSIS")
print("======================================")

total_events = len(
    results
)

events_with_brady = sum(
    1
    for r in results
    if r["below_100"] > 0
)

strong_brady_events = sum(
    1
    for r in results
    if r["classification"]
    == "STRONG BRADYCARDIA"
)

possible_brady_events = sum(
    1
    for r in results
    if r["classification"]
    == "POSSIBLE BRADYCARDIA"
)

print(
    "Total reference apnea events:",
    total_events
)

print(
    "Events with HR < 100 BPM:",
    events_with_brady
)

print(
    "Events with possible bradycardia:",
    possible_brady_events
)

print(
    "Events with strong bradycardia:",
    strong_brady_events
)


# ============================================================
# TABLE
# ============================================================

print()
print("======================================")
print("REFERENCE APNEA / BRADYCARDIA TABLE")
print("======================================")

print(
    "Event | Start | End | Duration | "
    "Before HR | During HR | Min HR | "
    "After HR | <100 | Brady"
)

print(
    "-" * 105
)


for r in results:

    before_text = (
        "NA"
        if np.isnan(r["before_hr"])
        else f"{r['before_hr']:.1f}"
    )

    during_text = (
        "NA"
        if np.isnan(r["during_hr"])
        else f"{r['during_hr']:.1f}"
    )

    min_text = (
        "NA"
        if np.isnan(r["min_hr"])
        else f"{r['min_hr']:.1f}"
    )

    after_text = (
        "NA"
        if np.isnan(r["after_hr"])
        else f"{r['after_hr']:.1f}"
    )

    if (
        r["classification"]
        == "STRONG BRADYCARDIA"
    ):

        brady_text = "YES"

    elif (
        r["classification"]
        == "POSSIBLE BRADYCARDIA"
    ):

        brady_text = "POSSIBLE"

    else:

        brady_text = "NO"

    print(
        f"{r['event']:5d} | "
        f"{r['start']/60:7.2f} | "
        f"{r['end']/60:7.2f} | "
        f"{r['duration']:8.2f} | "
        f"{before_text:9s} | "
        f"{during_text:9s} | "
        f"{min_text:7s} | "
        f"{after_text:8s} | "
        f"{r['below_100']:4d} | "
        f"{brady_text}"
    )


# ============================================================
# KEY RESULTS
# ============================================================

valid_during_means = [
    r["during_hr"]
    for r in results
    if not np.isnan(r["during_hr"])
]

valid_min_hr = [
    r["min_hr"]
    for r in results
    if not np.isnan(r["min_hr"])
]


print()
print("======================================")
print("KEY RESULTS")
print("======================================")

if valid_during_means:

    print(
        "Median mean HR during apnea:",
        round(
            float(
                np.median(
                    valid_during_means
                )
            ),
            2
        ),
        "BPM"
    )

else:

    print(
        "Median mean HR during apnea: NA"
    )


if valid_min_hr:

    print(
        "Median minimum HR during apnea:",
        round(
            float(
                np.median(
                    valid_min_hr
                )
            ),
            2
        ),
        "BPM"
    )

else:

    print(
        "Median minimum HR during apnea: NA"
    )


print()
print(
    "Actual ECG sampling frequency used:",
    ECG_FS
)

print(
    "ECG R-peaks used:",
    len(rpeaks)
)

print()
print("======================================")
print("DIAGNOSTIC COMPLETE")
print("======================================")