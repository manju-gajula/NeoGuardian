import os
import warnings
import numpy as np
import wfdb
from scipy.signal import butter, filtfilt, find_peaks, hilbert, medfilt

warnings.filterwarnings("ignore")

FS = 500.0
LOWCUT = 0.08
HIGHCUT = 1.2
FILTER_ORDER = 3

PEAK_MIN_DISTANCE = 0.65
PEAK_PROMINENCE_FACTOR = 0.12

REFERENCE_GAP_SEC = 20.0
REFERENCE_MERGE_GAP_SEC = 0.01

MIN_APNEA_SEC = 15.0
MAX_APNEA_SEC = 120.0

ENVELOPE_WINDOW_SEC = 10.0
BASELINE_WINDOW_SEC = 60.0

LONG_INTERVAL_SEC = 15.0
STRONG_INTERVAL_SEC = 20.0

SUPPRESSION_THRESHOLD = 0.55
STRONG_SUPPRESSION = 0.40

MATCH_OVERLAP = 0.20
MATCH_CENTER_SEC = 20.0

CHUNK_SECONDS = 120.0


def find_record():
    candidates = [
        os.path.join("data", "picsdb", "infant1_resp"),
        os.path.join("data", "picsdb", "infant1_resp"),
    ]
    for record in candidates:
        if os.path.exists(record + ".hea"):
            return os.path.abspath(record)
    raise FileNotFoundError(
        "Could not find data/picsdb/infant1_resp.hea"
    )


def load_respiration():
    print("======================================")
    print("LOADING RESPIRATION")
    print("======================================")

    record = find_record()
    info = wfdb.rdheader(record)

    print("Selected WFDB record:")
    print(record)
    print("Channels:", info.sig_name)
    print("Sampling frequency:", info.fs)

    resp_channel = None
    for i, name in enumerate(info.sig_name):
        if str(name).upper() == "RESP":
            resp_channel = i
            break

    if resp_channel is None:
        for i, name in enumerate(info.sig_name):
            if "RESP" in str(name).upper():
                resp_channel = i
                break

    if resp_channel is None:
        raise RuntimeError("RESP channel not found.")

    print()
    print("Selected respiration channel:")
    print(resp_channel, "-", info.sig_name[resp_channel])
    print()
    print("Loading respiration signal...")

    signal, fields = wfdb.rdsamp(record, channels=[resp_channel])

    respiration = np.asarray(signal[:, 0], dtype=np.float64)
    fs = float(fields["fs"])

    if abs(fs - FS) > 0.01:
        raise RuntimeError(
            f"Unexpected sampling frequency: {fs}"
        )

    finite = np.isfinite(respiration)
    if not np.all(finite):
        median = np.median(respiration[finite])
        respiration[~finite] = median

    print(f"Total samples: {len(respiration)}")
    print(f"Sampling frequency: {fs}")
    print(
        f"Duration: {len(respiration) / fs / 60:.1f} minutes"
    )

    return respiration


def butter_bandpass(lowcut, highcut, fs, order):
    nyq = fs * 0.5
    b, a = butter(
        order,
        [lowcut / nyq, highcut / nyq],
        btype="band"
    )
    return b, a


def bandpass_filter(signal, fs):
    print()
    print("Filtering respiration signal...")

    b, a = butter_bandpass(
        LOWCUT,
        HIGHCUT,
        fs,
        FILTER_ORDER
    )

    n = len(signal)
    chunk = int(CHUNK_SECONDS * fs)
    pad = int(10 * fs)

    if n < 5000000:
        return filtfilt(b, a, signal)

    print("Large signal detected - using chunked filtering.")

    output = np.empty_like(signal)

    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        left = max(0, start - pad)
        right = min(n, end + pad)

        filtered = filtfilt(
            b,
            a,
            signal[left:right]
        )

        l0 = start - left
        l1 = l0 + (end - start)

        output[start:end] = filtered[l0:l1]

    return output


def robust_amplitude(signal):
    q05, q95 = np.percentile(signal, [5, 95])
    return float(q95 - q05)


def detect_peaks(signal, fs):
    print()
    print("======================================")
    print("DETECTING RESPIRATORY PEAKS")
    print("======================================")

    amplitude = robust_amplitude(signal)

    prominence = max(
        amplitude * PEAK_PROMINENCE_FACTOR,
        np.finfo(float).eps
    )

    distance = int(PEAK_MIN_DISTANCE * fs)

    print(f"Robust amplitude: {amplitude:.4f}")
    print(f"Peak prominence: {prominence:.4f}")

    peaks, properties = find_peaks(
        signal,
        distance=distance,
        prominence=prominence
    )

    print()
    print(f"Detected respiration peaks: {len(peaks)}")

    return peaks


def respiratory_intervals(peaks, fs):
    intervals = np.diff(peaks) / fs

    print()
    print("======================================")
    print("RESPIRATORY INTERVAL ANALYSIS")
    print("======================================")

    if len(intervals) == 0:
        return intervals

    print(f"Respiratory intervals: {len(intervals)}")
    print(f"Minimum: {intervals.min():.2f} sec")
    print(f"Median: {np.median(intervals):.2f} sec")
    print(f"Maximum: {intervals.max():.2f} sec")
    print(
        f"Intervals >= 10 sec: "
        f"{np.sum(intervals >= 10)}"
    )
    print(
        f"Intervals >= 15 sec: "
        f"{np.sum(intervals >= 15)}"
    )
    print(
        f"Intervals >= 20 sec: "
        f"{np.sum(intervals >= 20)}"
    )

    return intervals


def calculate_envelope(signal, fs):
    analytic = hilbert(signal)
    envelope = np.abs(analytic)

    window = int(ENVELOPE_WINDOW_SEC * fs)
    window = max(window, 3)

    if window % 2 == 0:
        window += 1

    if window >= len(envelope):
        return envelope

    return medfilt(envelope, kernel_size=window)


def moving_median(signal, window):
    window = max(3, int(window))

    if window % 2 == 0:
        window += 1

    if window >= len(signal):
        return np.full_like(
            signal,
            np.median(signal)
        )

    return medfilt(signal, kernel_size=window)


def build_interval_candidates(peaks, fs):
    intervals = np.diff(peaks) / fs
    candidates = []

    for i, interval in enumerate(intervals):
        if interval < LONG_INTERVAL_SEC:
            continue

        start = peaks[i] / fs
        end = peaks[i + 1] / fs

        if end - start < MIN_APNEA_SEC:
            continue

        if end - start > MAX_APNEA_SEC:
            end = start + MAX_APNEA_SEC

        strength = (
            "strong_interval"
            if interval >= STRONG_INTERVAL_SEC
            else "moderate_interval"
        )

        candidates.append({
            "start": start,
            "end": end,
            "source": strength
        })

    return candidates


def build_envelope_candidates(signal, envelope, fs):
    print()
    print("Calculating respiration amplitude envelope...")

    n = len(signal)

    baseline_samples = int(
        BASELINE_WINDOW_SEC * fs
    )

    step = int(2 * fs)

    candidates = []

    for center in range(
        baseline_samples,
        n - baseline_samples,
        step
    ):
        left = center - int(15 * fs)
        right = center + int(15 * fs)

        if left < 0 or right >= n:
            continue

        local = envelope[left:right]

        if len(local) < 10:
            continue

        center_left = int(10 * fs)
        center_right = int(20 * fs)

        suppressed = local[center_left:center_right]

        if len(suppressed) == 0:
            continue

        baseline_left = max(
            0,
            center - baseline_samples
        )
        baseline_right = min(
            n,
            center + baseline_samples
        )

        baseline = envelope[
            baseline_left:baseline_right
        ]

        if len(baseline) == 0:
            continue

        baseline_value = np.percentile(
            baseline,
            60
        )

        suppressed_value = np.percentile(
            suppressed,
            25
        )

        if baseline_value <= 1e-10:
            continue

        ratio = (
            suppressed_value /
            baseline_value
        )

        if ratio > SUPPRESSION_THRESHOLD:
            continue

        start = (
            center - 5 * fs
        ) / fs

        end = (
            center + 5 * fs
        ) / fs

        candidates.append({
            "start": max(0.0, start),
            "end": min(n / fs, end),
            "source": "envelope",
            "suppression": ratio
        })

    return candidates


def merge_candidates(candidates):
    if not candidates:
        return []

    candidates = sorted(
        candidates,
        key=lambda x: x["start"]
    )

    merged = []

    for candidate in candidates:
        if not merged:
            merged.append(candidate.copy())
            continue

        previous = merged[-1]

        if candidate["start"] <= previous["end"] + 2.0:
            previous["end"] = max(
                previous["end"],
                candidate["end"]
            )

            if (
                previous.get("source") !=
                candidate.get("source")
            ):
                previous["source"] = "merged"

        else:
            merged.append(candidate.copy())

    return merged


def candidate_features(candidate, envelope, fs):
    start = max(
        0,
        int(candidate["start"] * fs)
    )

    end = min(
        len(envelope),
        int(candidate["end"] * fs)
    )

    if end <= start:
        return None

    segment = envelope[start:end]

    if len(segment) < 10:
        return None

    duration = (end - start) / fs

    context = int(30 * fs)

    left = max(0, start - context)
    right = min(
        len(envelope),
        end + context
    )

    surrounding = envelope[left:right]

    if len(surrounding) == 0:
        return None

    baseline = np.percentile(
        surrounding,
        70
    )

    suppressed = np.percentile(
        segment,
        25
    )

    suppression = (
        suppressed / baseline
        if baseline > 1e-10
        else 1.0
    )

    recovery_start = end
    recovery_end = min(
        len(envelope),
        end + int(15 * fs)
    )

    recovery = envelope[
        recovery_start:recovery_end
    ]

    if len(recovery) == 0:
        recovery_ratio = 0.0
    else:
        recovery_ratio = (
            np.percentile(recovery, 75) /
            baseline
            if baseline > 1e-10
            else 0.0
        )

    return {
        "duration": duration,
        "suppression": float(suppression),
        "recovery": float(recovery_ratio)
    }


def validate_candidates(
    candidates,
    envelope,
    fs
):
    validated = []

    for candidate in candidates:
        features = candidate_features(
            candidate,
            envelope,
            fs
        )

        if features is None:
            continue

        duration = features["duration"]
        suppression = features["suppression"]
        recovery = features["recovery"]

        if duration < MIN_APNEA_SEC:
            continue

        if duration > MAX_APNEA_SEC:
            continue

        interval_source = candidate[
            "source"
        ] in (
            "strong_interval",
            "moderate_interval"
        )

        strong = (
            suppression <= STRONG_SUPPRESSION
        )

        moderate = (
            suppression <= SUPPRESSION_THRESHOLD
        )

        if interval_source:
            if strong or (
                candidate["source"] ==
                "strong_interval"
                and moderate
            ):
                validated.append({
                    "start": candidate["start"],
                    "end": candidate["end"],
                    "duration": duration,
                    "suppression": suppression,
                    "recovery": recovery,
                    "source": candidate["source"]
                })

        elif moderate:
            validated.append({
                "start": candidate["start"],
                "end": candidate["end"],
                "duration": duration,
                "suppression": suppression,
                "recovery": recovery,
                "source": candidate["source"]
            })

    return merge_validated(validated)


def merge_validated(events):
    if not events:
        return []

    events = sorted(
        events,
        key=lambda x: x["start"]
    )

    merged = []

    for event in events:
        if not merged:
            merged.append(event.copy())
            continue

        previous = merged[-1]

        if event["start"] <= previous["end"] + 1.0:
            previous["end"] = max(
                previous["end"],
                event["end"]
            )

            previous["duration"] = (
                previous["end"] -
                previous["start"]
            )

            previous["suppression"] = min(
                previous["suppression"],
                event["suppression"]
            )

            previous["recovery"] = max(
                previous["recovery"],
                event["recovery"]
            )

            previous["source"] = "merged"

        else:
            merged.append(event.copy())

    return merged


def load_reference_apnea_events(record):
    print()
    print("======================================")
    print("LOADING REFERENCE RESPIRATION")
    print("======================================")

    annotation = wfdb.rdann(
        record,
        "resp"
    )

    print(
        f"Reference annotations: "
        f"{len(annotation.sample)}"
    )
    print(
        f"Reference annotation FS: "
        f"{annotation.fs}"
    )

    samples = np.asarray(
        annotation.sample,
        dtype=np.int64
    )

    if len(samples) < 2:
        raise RuntimeError(
            "Not enough .resp annotations."
        )

    times = samples / float(annotation.fs)

    gaps = np.diff(times)

    raw = []

    for i, gap in enumerate(gaps):
        if gap >= REFERENCE_GAP_SEC:
            raw.append(
                (
                    times[i],
                    times[i + 1]
                )
            )

    merged = []

    for start, end in raw:
        if not merged:
            merged.append(
                [start, end]
            )
            continue

        previous = merged[-1]

        if (
            start <=
            previous[1] +
            REFERENCE_MERGE_GAP_SEC
        ):
            previous[1] = max(
                previous[1],
                end
            )
        else:
            merged.append(
                [start, end]
            )

    events = []

    for start, end in merged:
        duration = end - start

        if duration >= REFERENCE_GAP_SEC:
            events.append({
                "start": float(start),
                "end": float(end),
                "duration": float(duration)
            })

    print()
    print("======================================")
    print("REFERENCE APNEA EVENTS")
    print("======================================")

    print(
        f"Reference apnea events: "
        f"{len(events)}"
    )

    for i, event in enumerate(events, 1):
        print(
            f"{i}. "
            f"{event['start'] / 60:.2f} -> "
            f"{event['end'] / 60:.2f} min | "
            f"Duration: "
            f"{event['duration']:.2f} sec"
        )

    if len(events) != 40:
        print()
        print(
            "WARNING: reference count is "
            f"{len(events)}, not 40."
        )
        print(
            "The detector will continue, "
            "but the reference reconstruction "
            "did not reproduce the expected V7 "
            "count."
        )

    return events


def overlap(a, b):
    start = max(
        a["start"],
        b["start"]
    )

    end = min(
        a["end"],
        b["end"]
    )

    return max(
        0.0,
        end - start
    )


def event_match_score(detected, reference):
    ov = overlap(
        detected,
        reference
    )

    d1 = detected["end"] - detected["start"]
    d2 = reference["end"] - reference["start"]

    union = (
        d1 +
        d2 -
        ov
    )

    iou = (
        ov / union
        if union > 0
        else 0.0
    )

    center_d = abs(
        (
            detected["start"] +
            detected["end"]
        ) / 2 -
        (
            reference["start"] +
            reference["end"]
        ) / 2
    )

    return iou, center_d


def evaluate(
    detected,
    reference
):
    matches = []
    used_reference = set()

    ordered = sorted(
        detected,
        key=lambda x: x["start"]
    )

    for detected_event in ordered:
        best = None

        for j, reference_event in enumerate(
            reference
        ):
            if j in used_reference:
                continue

            iou, center_d = event_match_score(
                detected_event,
                reference_event
            )

            if (
                iou >= MATCH_OVERLAP
                or center_d <= MATCH_CENTER_SEC
            ):
                score = (
                    iou,
                    -center_d
                )

                if (
                    best is None
                    or score > best[0]
                ):
                    best = (
                        score,
                        j,
                        iou,
                        center_d
                    )

        if best is not None:
            _, j, iou, center_d = best

            used_reference.add(j)

            matches.append(
                (
                    detected_event,
                    reference[j],
                    iou,
                    center_d
                )
            )

    tp = len(matches)
    fp = len(detected) - tp
    fn = len(reference) - tp

    precision = (
        tp / (tp + fp)
        if tp + fp > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return (
        matches,
        tp,
        fp,
        fn,
        precision,
        recall,
        f1
    )


def print_results(
    detected,
    reference
):
    (
        matches,
        tp,
        fp,
        fn,
        precision,
        recall,
        f1
    ) = evaluate(
        detected,
        reference
    )

    print()
    print("======================================")
    print("DETECTION RESULTS")
    print("======================================")

    print(
        f"Reference apnea events: "
        f"{len(reference)}"
    )
    print(
        f"Detected apnea events: "
        f"{len(detected)}"
    )
    print(f"True Positives: {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1-score: {f1:.3f}")

    print()
    print("======================================")
    print("MATCHED EVENTS")
    print("======================================")

    for i, (
        detected_event,
        reference_event,
        iou,
        center_d
    ) in enumerate(matches, 1):

        print()
        print(f"{i}.")
        print(
            f"Detected: "
            f"{detected_event['start'] / 60:.2f} -> "
            f"{detected_event['end'] / 60:.2f} min"
        )
        print(
            f"Reference: "
            f"{reference_event['start'] / 60:.2f} -> "
            f"{reference_event['end'] / 60:.2f} min"
        )
        print(
            f"Center difference: "
            f"{center_d:.2f} sec"
        )
        print(
            f"Overlap: {iou:.3f}"
        )

    print()
    print("======================================")
    print("FINAL SUMMARY")
    print("======================================")

    print(
        f"Detected respiration peaks: "
        f"{len(peak_indices)}"
    )
    print(
        f"Reference apnea events: "
        f"{len(reference)}"
    )
    print(
        f"Detected apnea events: "
        f"{len(detected)}"
    )
    print(f"True positives: {tp}")
    print(f"False positives: {fp}")
    print(f"False negatives: {fn}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1-score: {f1:.3f}")


def main():
    print("======================================")
    print("HYBRID APNEA DETECTOR - V8.1")
    print("======================================")

    global peak_indices

    respiration = load_respiration()

    filtered = bandpass_filter(
        respiration,
        FS
    )

    peak_indices = detect_peaks(
        filtered,
        FS
    )

    respiratory_intervals(
        peak_indices,
        FS
    )

    envelope = calculate_envelope(
        filtered,
        FS
    )

    reference = load_reference_apnea_events(
        find_record()
    )

    print()
    print("======================================")
    print("GENERATING APNEA CANDIDATES")
    print("======================================")

    interval_candidates = (
        build_interval_candidates(
            peak_indices,
            FS
        )
    )

    envelope_candidates = (
        build_envelope_candidates(
            filtered,
            envelope,
            FS
        )
    )

    all_candidates = (
        interval_candidates +
        envelope_candidates
    )

    merged_candidates = merge_candidates(
        all_candidates
    )

    print(
        f"Long-interval candidates: "
        f"{len(interval_candidates)}"
    )
    print(
        f"Envelope candidates: "
        f"{len(envelope_candidates)}"
    )
    print(
        f"Merged candidates: "
        f"{len(merged_candidates)}"
    )

    print()
    print("======================================")
    print("VALIDATING APNEA CANDIDATES")
    print("======================================")

    detected = validate_candidates(
        merged_candidates,
        envelope,
        FS
    )

    print(
        f"Validated apnea events: "
        f"{len(detected)}"
    )

    print()
    print("======================================")
    print("FINAL APNEA EVENTS")
    print("======================================")

    for i, event in enumerate(
        detected,
        1
    ):
        print()
        print(f"Event {i}")
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
            f"{event['suppression']:.3f}"
        )
        print(
            f"Recovery ratio: "
            f"{event['recovery']:.3f}"
        )
        print(
            f"Source: "
            f"{event['source']}"
        )

    print_results(
        detected,
        reference
    )

    print()
    print(
        "======================================"
    )
    print(
        "Hybrid V8.1 apnea analysis complete."
    )


if __name__ == "__main__":
    main()