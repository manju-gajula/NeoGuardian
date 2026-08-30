import wfdb
import numpy as np
from scipy.signal import butter, sosfiltfilt, find_peaks


# ============================================================
# SETTINGS
# ============================================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

# Windows to inspect
WINDOWS = [
    ("Known event - 218 min", 217.0, 220.0),
    ("Missed event - 853 min", 852.0, 855.0),
    ("Missed events - 1019 min", 1018.0, 1022.0),
    ("Missed events - 1024 min", 1023.0, 1028.5),
    ("Missed events - 1031 min", 1030.0, 1035.0),
    ("Correct event - 1622 min", 1621.0, 1624.0),
    ("Correct event - 2140 min", 2139.0, 2142.0),
    ("Known event - 2463 min", 2462.0, 2465.0),
]

MIN_BREATH_DISTANCE = 1.5

PEAK_PROMINENCE_FACTOR = 0.25

MIN_VALID_INTERVAL = 1.0

APNEA_THRESHOLD = 20.0


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

print(
    "Total samples:",
    len(signal)
)

print(
    "Duration:",
    round(len(signal) / FS / 60, 2),
    "minutes"
)


# ============================================================
# FILTER
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
# LOAD REFERENCE ANNOTATIONS
# ============================================================

print()
print("Loading reference respiration annotations...")

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

print(
    "Reference annotations:",
    len(reference_times)
)


# ============================================================
# REFERENCE APNEA EVENTS
# ============================================================

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
# DIAGNOSTIC WINDOWS
# ============================================================

print()
print("======================================")
print("APNEA DETECTION DIAGNOSTICS")
print("======================================")


for window_name, start_min, end_min in WINDOWS:

    start_sec = start_min * 60
    end_sec = end_min * 60

    start_sample = int(
        start_sec * FS
    )

    end_sample = int(
        end_sec * FS
    )

    chunk = filtered[
        start_sample:end_sample
    ]

    print()
    print("======================================")
    print(window_name)
    print(
        f"Window: {start_min:.2f} - "
        f"{end_min:.2f} min"
    )
    print("======================================")


    # --------------------------------------------------------
    # Signal statistics
    # --------------------------------------------------------

    signal_min = np.min(chunk)
    signal_max = np.max(chunk)
    signal_std = np.std(chunk)

    median_value = np.median(chunk)

    mad = np.median(
        np.abs(
            chunk - median_value
        )
    )

    robust_std = (
        1.4826 * mad
    )

    if robust_std <= 1e-12:
        robust_std = signal_std

    if robust_std <= 1e-12:
        robust_std = 1.0


    print()
    print("SIGNAL STATISTICS")

    print(
        "Minimum:",
        round(signal_min, 6)
    )

    print(
        "Maximum:",
        round(signal_max, 6)
    )

    print(
        "Standard deviation:",
        round(signal_std, 6)
    )

    print(
        "Robust standard deviation:",
        round(robust_std, 6)
    )


    # --------------------------------------------------------
    # Multiple prominence levels
    # --------------------------------------------------------

    print()
    print("PEAK DETECTION COMPARISON")

    distance = int(
        MIN_BREATH_DISTANCE * FS
    )

    prominence_factors = [
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.40,
        0.50
    ]

    for factor in prominence_factors:

        prominence = (
            factor
            * robust_std
        )

        peaks, _ = find_peaks(
            chunk,
            distance=distance,
            prominence=prominence
        )

        print(
            f"Prominence factor "
            f"{factor:.2f}: "
            f"{len(peaks)} peaks"
        )


    # --------------------------------------------------------
    # Use current detector setting
    # --------------------------------------------------------

    prominence = (
        PEAK_PROMINENCE_FACTOR
        * robust_std
    )

    peaks, properties = find_peaks(
        chunk,
        distance=distance,
        prominence=prominence
    )


    print()
    print("CURRENT DETECTOR")

    print(
        "Prominence:",
        round(prominence, 6)
    )

    print(
        "Detected peaks:",
        len(peaks)
    )


    # --------------------------------------------------------
    # Respiratory intervals
    # --------------------------------------------------------

    if len(peaks) >= 2:

        intervals = (
            np.diff(peaks)
            / FS
        )

        valid_intervals = intervals[
            intervals >= MIN_VALID_INTERVAL
        ]

    else:

        intervals = np.array([])

        valid_intervals = np.array([])


    print()
    print("RESPIRATORY INTERVALS")

    if len(valid_intervals) > 0:

        print(
            "Count:",
            len(valid_intervals)
        )

        print(
            "Minimum:",
            round(
                np.min(valid_intervals),
                3
            ),
            "sec"
        )

        print(
            "Median:",
            round(
                np.median(valid_intervals),
                3
            ),
            "sec"
        )

        print(
            "Maximum:",
            round(
                np.max(valid_intervals),
                3
            ),
            "sec"
        )

        print(
            "Intervals >= 10 sec:",
            np.sum(
                valid_intervals >= 10
            )
        )

        print(
            "Intervals >= 20 sec:",
            np.sum(
                valid_intervals >= 20
            )
        )

    else:

        print(
            "No valid intervals."
        )


    # --------------------------------------------------------
    # Detected apnea candidates
    # --------------------------------------------------------

    print()
    print("DETECTED APNEA CANDIDATES")

    detected_events = []

    if len(peaks) >= 2:

        for i, interval in enumerate(
            intervals
        ):

            if interval < MIN_VALID_INTERVAL:
                continue

            if interval >= APNEA_THRESHOLD:

                event_start = (
                    start_sec
                    + peaks[i] / FS
                )

                event_end = (
                    start_sec
                    + peaks[i + 1] / FS
                )

                detected_events.append(
                    (
                        event_start,
                        event_end
                    )
                )

    if detected_events:

        for i, (
            event_start,
            event_end
        ) in enumerate(
            detected_events,
            start=1
        ):

            print(
                f"{i}. "
                f"{event_start / 60:.3f} → "
                f"{event_end / 60:.3f} min | "
                f"Duration: "
                f"{event_end - event_start:.2f} sec"
            )

    else:

        print(
            "No detected apnea candidates."
        )


    # --------------------------------------------------------
    # Reference events in this window
    # --------------------------------------------------------

    print()
    print("REFERENCE APNEA EVENTS")

    window_reference = []

    for ref_start, ref_end in reference_apneas:

        if (
            ref_end >= start_sec
            and
            ref_start <= end_sec
        ):

            window_reference.append(
                (
                    ref_start,
                    ref_end
                )
            )


    if window_reference:

        for i, (
            ref_start,
            ref_end
        ) in enumerate(
            window_reference,
            start=1
        ):

            print(
                f"{i}. "
                f"{ref_start / 60:.3f} → "
                f"{ref_end / 60:.3f} min | "
                f"Duration: "
                f"{ref_end - ref_start:.2f} sec"
            )

    else:

        print(
            "No reference apnea events "
            "in this window."
        )


# ============================================================
# FINAL
# ============================================================

print()
print("======================================")
print("DIAGNOSTIC COMPLETE")
print("======================================")