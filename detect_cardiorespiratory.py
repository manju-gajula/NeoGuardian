import wfdb
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt, find_peaks


# ============================================================
# SETTINGS
# ============================================================

RESP_RECORD = "data/picsdb/infant1_resp"
ECG_RECORD = "data/picsdb/infant1_ecg"

RESP_FS = 500
ECG_FS = 250

# Respiratory filtering
LOWCUT = 0.1
HIGHCUT = 0.8

# Minimum distance between respiratory peaks
MIN_BREATH_INTERVAL = 1.5

# Peak detection strength
RESP_PROMINENCE = 0.60

# Event thresholds
RESP_PAUSE_THRESHOLD = 10.0
APNEA_THRESHOLD = 20.0

# Bradycardia threshold
BRADYCARDIA_THRESHOLD = 100.0

# Minimum number of low-HR measurements required
MIN_BRADY_READINGS = 2

# For full-record processing
CHUNK_DURATION_SECONDS = 600


# ============================================================
# RESPIRATION FILTER
# ============================================================

def create_resp_filter():

    nyquist = RESP_FS / 2

    low = LOWCUT / nyquist
    high = HIGHCUT / nyquist

    sos = butter(
        4,
        [low, high],
        btype="band",
        output="sos"
    )

    return sos


# ============================================================
# DETECT RESPIRATION PEAKS IN ONE CHUNK
# ============================================================

def detect_respiration_chunk(
    signal,
    start_sample,
    sos
):

    filtered = sosfiltfilt(
        sos,
        signal
    )

    filtered = (
        filtered
        - np.mean(filtered)
    )

    std = np.std(filtered)

    if std > 0:
        filtered = filtered / std

    min_distance = int(
        MIN_BREATH_INTERVAL * RESP_FS
    )

    peaks, properties = find_peaks(
        filtered,
        distance=min_distance,
        prominence=RESP_PROMINENCE
    )

    global_peaks = (
        peaks
        + start_sample
    )

    return global_peaks


# ============================================================
# LOAD RESPIRATION PEAKS ACROSS WHOLE RECORD
# ============================================================

def detect_all_respiratory_peaks():

    print("\n======================================")
    print("RESPIRATION ANALYSIS")
    print("======================================")

    record_info = wfdb.rdheader(
        RESP_RECORD
    )

    total_samples = (
        record_info.sig_len
    )

    print(
        "Total respiration samples:",
        total_samples
    )

    print(
        "Respiration sampling frequency:",
        RESP_FS
    )

    chunk_samples = int(
        CHUNK_DURATION_SECONDS
        * RESP_FS
    )

    sos = create_resp_filter()

    all_peaks = []

    current_start = 0

    chunk_number = 0

    while current_start < total_samples:

        chunk_number += 1

        current_end = min(
            current_start + chunk_samples,
            total_samples
        )

        print(
            f"Processing respiration chunk "
            f"{chunk_number}: "
            f"{current_start / RESP_FS / 60:.1f} "
            f"to "
            f"{current_end / RESP_FS / 60:.1f} min"
        )

        record = wfdb.rdrecord(
            RESP_RECORD,
            sampfrom=current_start,
            sampto=current_end,
            channels=[0]
        )

        signal = record.p_signal[:, 0]

        peaks = detect_respiration_chunk(
            signal,
            current_start,
            sos
        )

        all_peaks.extend(
            peaks.tolist()
        )

        current_start = current_end

    all_peaks = np.asarray(
        all_peaks,
        dtype=int
    )

    # Sort
    all_peaks = np.sort(
        all_peaks
    )

    # Remove duplicate peaks
    if len(all_peaks) > 1:

        keep = np.concatenate(
            [
                [True],
                np.diff(all_peaks) > 1
            ]
        )

        all_peaks = all_peaks[keep]

    print(
        "\nTotal detected respiration peaks:",
        len(all_peaks)
    )

    return all_peaks


# ============================================================
# LOAD ECG R-PEAKS
# ============================================================

def load_rpeaks():

    print("\n======================================")
    print("ECG R-PEAK ANALYSIS")
    print("======================================")

    annotations = wfdb.rdann(
        ECG_RECORD,
        "qrsc"
    )

    rpeaks = np.asarray(
        annotations.sample
    )

    print(
        "Total ECG R-peaks:",
        len(rpeaks)
    )

    return rpeaks


# ============================================================
# FIND RESPIRATORY PAUSES
# ============================================================

def find_respiratory_pauses(
    resp_peaks
):

    resp_times = (
        resp_peaks
        / RESP_FS
    )

    intervals = np.diff(
        resp_times
    )

    pauses = []

    for i, interval in enumerate(
        intervals
    ):

        if interval >= RESP_PAUSE_THRESHOLD:

            pause = {
                "start": resp_times[i],
                "end": resp_times[i + 1],
                "duration": interval
            }

            pauses.append(
                pause
            )

    return pauses


# ============================================================
# CALCULATE HEART RATE
# ============================================================

def calculate_heart_rate(
    rpeaks
):

    rpeak_times = (
        rpeaks
        / ECG_FS
    )

    rr = np.diff(
        rpeak_times
    )

    rr_times = (
        rpeak_times[1:]
    )

    # Remove impossible RR intervals
    valid = (
        (rr >= 0.20)
        &
        (rr <= 2.0)
    )

    rr = rr[valid]
    rr_times = rr_times[valid]

    heart_rate = (
        60.0 / rr
    )

    return (
        rr_times,
        heart_rate
    )


# ============================================================
# ANALYZE ONE RESPIRATORY PAUSE
# ============================================================

def analyze_pause(
    pause,
    rr_times,
    heart_rate
):

    start = pause["start"]
    end = pause["end"]

    mask = (
        (rr_times >= start)
        &
        (rr_times <= end)
    )

    event_hr = (
        heart_rate[mask]
    )

    if len(event_hr) == 0:

        return {
            **pause,
            "min_hr": None,
            "mean_hr": None,
            "brady_readings": 0,
            "brady_fraction": 0.0,
            "apnea": pause["duration"] >= APNEA_THRESHOLD,
            "combined": False
        }

    min_hr = np.min(
        event_hr
    )

    mean_hr = np.mean(
        event_hr
    )

    brady_readings = np.sum(
        event_hr
        < BRADYCARDIA_THRESHOLD
    )

    brady_fraction = (
        brady_readings
        / len(event_hr)
    )

    apnea = (
        pause["duration"]
        >= APNEA_THRESHOLD
    )

    # Combined event requires:
    # 1. Respiratory pause >= 20 sec
    # 2. At least 2 HR readings below 100 BPM
    combined = (
        apnea
        and
        brady_readings
        >= MIN_BRADY_READINGS
    )

    return {
        **pause,
        "min_hr": min_hr,
        "mean_hr": mean_hr,
        "brady_readings": int(
            brady_readings
        ),
        "brady_fraction": brady_fraction,
        "apnea": apnea,
        "combined": combined
    }


# ============================================================
# MERGE NEARBY COMBINED EVENTS
# ============================================================

def merge_events(
    events
):

    if len(events) <= 1:
        return events

    events = sorted(
        events,
        key=lambda x: x["start"]
    )

    merged = [
        events[0].copy()
    ]

    for current in events[1:]:

        previous = merged[-1]

        gap = (
            current["start"]
            - previous["end"]
        )

        # Merge events separated by <= 5 sec
        if gap <= 5.0:

            previous["end"] = max(
                previous["end"],
                current["end"]
            )

            previous["duration"] = (
                previous["end"]
                - previous["start"]
            )

            previous["min_hr"] = min(
                previous["min_hr"],
                current["min_hr"]
            )

            previous["mean_hr"] = np.mean(
                [
                    previous["mean_hr"],
                    current["mean_hr"]
                ]
            )

            previous["brady_readings"] += (
                current["brady_readings"]
            )

        else:

            merged.append(
                current.copy()
            )

    return merged


# ============================================================
# MAIN
# ============================================================

print("\n")
print("########################################")
print("#  NEOGUARDIAN CARDIORESPIRATORY       #")
print("#  EVENT DETECTOR                       #")
print("########################################")


# ------------------------------------------------------------
# 1. Respiration
# ------------------------------------------------------------

resp_peaks = (
    detect_all_respiratory_peaks()
)


# ------------------------------------------------------------
# 2. ECG
# ------------------------------------------------------------

rpeaks = (
    load_rpeaks()
)


# ------------------------------------------------------------
# 3. Respiratory pauses
# ------------------------------------------------------------

pauses = (
    find_respiratory_pauses(
        resp_peaks
    )
)


print("\n======================================")
print("RESPIRATORY PAUSE RESULTS")
print("======================================")

print(
    "Respiratory pauses >= 10 sec:",
    len(pauses)
)

apnea_pauses = [
    p
    for p in pauses
    if p["duration"] >= APNEA_THRESHOLD
]

print(
    "Respiratory pauses >= 20 sec:",
    len(apnea_pauses)
)


# ------------------------------------------------------------
# 4. Heart rate
# ------------------------------------------------------------

rr_times, heart_rate = (
    calculate_heart_rate(
        rpeaks
    )
)


print("\n======================================")
print("HEART RATE RESULTS")
print("======================================")

print(
    "Valid RR intervals:",
    len(heart_rate)
)

print(
    "Mean HR:",
    round(
        np.mean(heart_rate),
        2
    ),
    "BPM"
)

print(
    "Median HR:",
    round(
        np.median(heart_rate),
        2
    ),
    "BPM"
)


# ------------------------------------------------------------
# 5. Analyze pauses
# ------------------------------------------------------------

results = []

for pause in pauses:

    result = analyze_pause(
        pause,
        rr_times,
        heart_rate
    )

    results.append(
        result
    )


# ------------------------------------------------------------
# 6. Print apnea events
# ------------------------------------------------------------

print("\n======================================")
print("APNEA-DURATION EVENTS")
print("======================================")


apnea_results = [
    r
    for r in results
    if r["apnea"]
]


print(
    "Total apnea-duration events:",
    len(apnea_results)
)


for i, event in enumerate(
    apnea_results,
    start=1
):

    print(
        f"\nEvent {i}"
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

    if event["min_hr"] is not None:

        print(
            f"Minimum HR: "
            f"{event['min_hr']:.2f} BPM"
        )

        print(
            f"Mean HR: "
            f"{event['mean_hr']:.2f} BPM"
        )

        print(
            f"HR < {BRADYCARDIA_THRESHOLD:.0f}: "
            f"{event['brady_readings']}"
        )


# ------------------------------------------------------------
# 7. Combined events
# ------------------------------------------------------------

combined_events = [
    r
    for r in results
    if r["combined"]
]


combined_events = merge_events(
    combined_events
)


print("\n======================================")
print("COMBINED CARDIORESPIRATORY EVENTS")
print("======================================")


print(
    "Combined events:",
    len(combined_events)
)


if len(combined_events) == 0:

    print(
        "\nNo combined apnea + "
        "bradycardia events detected."
    )

else:

    for i, event in enumerate(
        combined_events,
        start=1
    ):

        print(
            f"\nEvent {i}"
        )

        print(
            "--------------------------------------"
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
            f"Minimum HR: "
            f"{event['min_hr']:.2f} BPM"
        )

        print(
            f"Mean HR: "
            f"{event['mean_hr']:.2f} BPM"
        )

        print(
            f"Bradycardia readings: "
            f"{event['brady_readings']}"
        )

        print(
            "Classification: "
            "APNEA + BRADYCARDIA"
        )


# ============================================================
# SUMMARY
# ============================================================

print("\n======================================")
print("FINAL SUMMARY")
print("======================================")

print(
    "Respiration peaks:",
    len(resp_peaks)
)

print(
    "Respiratory pauses >= 10 sec:",
    len(pauses)
)

print(
    "Apnea-duration events >= 20 sec:",
    len(apnea_results)
)

print(
    "Combined apnea + bradycardia events:",
    len(combined_events)
)

print("\nAnalysis complete.")