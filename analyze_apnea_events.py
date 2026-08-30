import wfdb
import numpy as np
from scipy.signal import butter, sosfiltfilt, hilbert


# ============================================================
# SETTINGS
# ============================================================

RECORD_PATH = "data/picsdb/infant1_resp"

FS = 500

APNEA_THRESHOLD = 20.0

# How much signal to inspect around each reference event
BEFORE_SECONDS = 30.0
AFTER_SECONDS = 30.0


# ============================================================
# LOAD REFERENCE ANNOTATIONS
# ============================================================

print("Loading PICSDB respiration annotations...")

annotations = wfdb.rdann(
    RECORD_PATH,
    "resp"
)

reference_samples = np.asarray(
    annotations.sample,
    dtype=int
)

reference_times = (
    reference_samples / annotations.fs
)

print("Reference annotations loaded!")
print(
    "Total annotations:",
    len(reference_times)
)


# ============================================================
# FIND REFERENCE APNEA EVENTS
# ============================================================

intervals = np.diff(
    reference_times
)

reference_apneas = []

for i, interval in enumerate(intervals):

    if interval >= APNEA_THRESHOLD:

        start = reference_times[i]
        end = reference_times[i + 1]

        reference_apneas.append(
            (
                start,
                end
            )
        )


print()
print("======================================")
print("REFERENCE APNEA EVENTS")
print("======================================")

print(
    "Total reference apnea events:",
    len(reference_apneas)
)


# ============================================================
# RESPIRATION FILTER
# ============================================================

sos = butter(
    4,
    [0.05, 2.0],
    btype="bandpass",
    fs=FS,
    output="sos"
)


# ============================================================
# LOAD SIGNAL AROUND EVENT
# ============================================================

def analyze_event(
    start,
    end
):

    window_start = max(
        0,
        start - BEFORE_SECONDS
    )

    window_end = (
        end + AFTER_SECONDS
    )

    sampfrom = int(
        window_start * FS
    )

    sampto = int(
        window_end * FS
    )

    record = wfdb.rdrecord(
        RECORD_PATH,
        sampfrom=sampfrom,
        sampto=sampto,
        channels=[0]
    )

    signal = np.asarray(
        record.p_signal[:, 0],
        dtype=float
    )

    signal = np.nan_to_num(
        signal
    )

    # Remove DC
    signal = (
        signal
        - np.median(signal)
    )

    # Filter respiration
    filtered = sosfiltfilt(
        sos,
        signal
    )

    # Envelope
    analytic = hilbert(
        filtered
    )

    envelope = np.abs(
        analytic
    )

    # --------------------------------------------------------
    # Regions
    # --------------------------------------------------------

    relative_start = BEFORE_SECONDS

    relative_end = (
        BEFORE_SECONDS
        + (end - start)
    )

    start_sample = int(
        relative_start * FS
    )

    end_sample = int(
        relative_end * FS
    )

    start_sample = max(
        0,
        min(
            start_sample,
            len(envelope)
        )
    )

    end_sample = max(
        start_sample,
        min(
            end_sample,
            len(envelope)
        )
    )

    during = envelope[
        start_sample:end_sample
    ]

    before = envelope[
        max(
            0,
            start_sample
            - int(20 * FS)
        ):
        start_sample
    ]

    after_start = min(
        len(envelope),
        end_sample
    )

    after_end = min(
        len(envelope),
        after_start
        + int(20 * FS)
    )

    after = envelope[
        after_start:after_end
    ]

    if len(during) == 0:
        return None

    if len(before) == 0:
        return None

    if len(after) == 0:
        return None

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    before_median = np.median(
        before
    )

    during_median = np.median(
        during
    )

    after_median = np.median(
        after
    )

    before_mean = np.mean(
        before
    )

    during_mean = np.mean(
        during
    )

    after_mean = np.mean(
        after
    )

    suppression_ratio = (
        during_median
        / max(
            before_median,
            1e-12
        )
    )

    recovery_ratio = (
        after_median
        / max(
            before_median,
            1e-12
        )
    )

    return {
        "start": start,
        "end": end,
        "duration": end - start,
        "before_median": before_median,
        "during_median": during_median,
        "after_median": after_median,
        "before_mean": before_mean,
        "during_mean": during_mean,
        "after_mean": after_mean,
        "suppression_ratio": suppression_ratio,
        "recovery_ratio": recovery_ratio
    }


# ============================================================
# ANALYZE ALL EVENTS
# ============================================================

results = []

print()
print("Analyzing reference apnea signals...")

for index, (
    start,
    end
) in enumerate(
    reference_apneas,
    start=1
):

    result = analyze_event(
        start,
        end
    )

    if result is not None:

        results.append(
            result
        )

    print(
        f"Processed event "
        f"{index}/{len(reference_apneas)}"
    )


# ============================================================
# PRINT RESULTS
# ============================================================

print()
print("======================================")
print("REFERENCE APNEA SIGNAL ANALYSIS")
print("======================================")

print(
    "Successfully analyzed:",
    len(results)
)


for index, result in enumerate(
    results,
    start=1
):

    print()
    print(
        f"Event {index}"
    )

    print(
        f"Start: "
        f"{result['start'] / 60:.2f} min"
    )

    print(
        f"End: "
        f"{result['end'] / 60:.2f} min"
    )

    print(
        f"Duration: "
        f"{result['duration']:.2f} sec"
    )

    print(
        f"Before amplitude: "
        f"{result['before_median']:.6f}"
    )

    print(
        f"During amplitude: "
        f"{result['during_median']:.6f}"
    )

    print(
        f"After amplitude: "
        f"{result['after_median']:.6f}"
    )

    print(
        f"Suppression ratio: "
        f"{result['suppression_ratio']:.3f}"
    )

    print(
        f"Recovery ratio: "
        f"{result['recovery_ratio']:.3f}"
    )


# ============================================================
# SUMMARY STATISTICS
# ============================================================

if results:

    suppression = np.array(
        [
            r["suppression_ratio"]
            for r in results
        ]
    )

    durations = np.array(
        [
            r["duration"]
            for r in results
        ]
    )

    print()
    print("======================================")
    print("APNEA CHARACTERISTICS")
    print("======================================")

    print(
        "Duration median:",
        round(
            np.median(durations),
            2
        ),
        "sec"
    )

    print(
        "Duration minimum:",
        round(
            np.min(durations),
            2
        ),
        "sec"
    )

    print(
        "Duration maximum:",
        round(
            np.max(durations),
            2
        ),
        "sec"
    )

    print(
        "Suppression ratio median:",
        round(
            np.median(suppression),
            3
        )
    )

    print(
        "Suppression ratio minimum:",
        round(
            np.min(suppression),
            3
        )
    )

    print(
        "Suppression ratio maximum:",
        round(
            np.max(suppression),
            3
        )
    )

    print()
    print(
        "Suppression ratio percentiles:"
    )

    for percentile in [
        10,
        25,
        50,
        75,
        90
    ]:

        print(
            f"{percentile}th percentile:",
            round(
                np.percentile(
                    suppression,
                    percentile
                ),
                3
            )
        )


print()
print("======================================")
print("DIAGNOSTIC COMPLETE")
print("======================================")