"""
NeoGuardian Waveform Features & Signal Reader
Provides high-performance chunked window reading, downsampling, and caching
for PICSDB Respiration (500 Hz) and ECG (250 Hz) signals.
"""

import os
import functools
import wfdb
import numpy as np
from typing import Tuple, Dict, Any, Optional, List


def get_picsdb_path(infant_id: str, modality: str = "resp") -> str:
    """
    Resolves the absolute path to a PICSDB record.
    infant_id: e.g. 'infant1' or '1'
    modality: 'resp' or 'ecg'
    """
    clean_id = infant_id.lower().replace("_resp", "").replace("_ecg", "")
    if clean_id.isdigit():
        clean_id = f"infant{clean_id}"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    picsdb_dir = os.path.join(project_root, "data", "picsdb")

    record_name = f"{clean_id}_{modality}"
    record_path = os.path.join(picsdb_dir, record_name)

    if not os.path.exists(record_path + ".hea"):
        raise FileNotFoundError(f"Record {record_name} not found in {picsdb_dir}")

    return record_path


@functools.lru_cache(maxsize=32)
def load_picsdb_header(record_path: str):
    return wfdb.rdheader(record_path)


def load_respiration_window(
    infant_id: str,
    start_sec: float = 13080.0,
    duration_sec: float = 120.0,
    target_fs: float = 15.0
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Loads a slice of the 500 Hz respiration waveform and downsamples it for the UI.
    Returns:
        time_axis (np.ndarray): time in seconds
        signal (np.ndarray): filtered/normalized respiration amplitude
        original_fs (float): 500.0
    """
    record_path = get_picsdb_path(infant_id, "resp")
    header = load_picsdb_header(record_path)
    fs = float(header.fs)

    total_samples = header.sig_len
    start_sample = max(0, int(start_sec * fs))
    end_sample = min(total_samples, int((start_sec + duration_sec) * fs))

    # If requested window is outside bounds, clamp to known active region
    if start_sample >= total_samples:
        start_sample = max(0, total_samples - int(duration_sec * fs))
        end_sample = total_samples

    signal_chunk, fields = wfdb.rdsamp(
        record_path,
        sampfrom=start_sample,
        sampto=end_sample,
        channels=[0]
    )

    raw_signal = np.asarray(signal_chunk[:, 0], dtype=np.float64)

    # Clean NaNs/Infs
    finite_mask = np.isfinite(raw_signal)
    if not np.all(finite_mask):
        median_val = np.median(raw_signal[finite_mask]) if np.any(finite_mask) else 0.0
        raw_signal[~finite_mask] = median_val

    # Downsampling factor
    downsample_factor = max(1, int(fs / target_fs))
    downsampled_signal = raw_signal[::downsample_factor]
    
    # Calculate time coordinates in seconds
    raw_times = (np.arange(len(raw_signal)) + start_sample) / fs
    downsampled_times = raw_times[::downsample_factor]

    return downsampled_times, downsampled_signal, fs


@functools.lru_cache(maxsize=32)
def load_ecg_rpeaks(infant_id: str) -> Tuple[np.ndarray, float]:
    """
    Loads verified ECG R-peaks from the .qrsc annotation file.
    Cached in memory for instantaneous sub-millisecond responses.
    """
    record_path = get_picsdb_path(infant_id, "ecg")
    ann = wfdb.rdann(record_path, "qrsc")
    fs = float(ann.fs)

    peak_samples = np.asarray(ann.sample, dtype=np.float64)
    rpeak_times = peak_samples / fs

    return rpeak_times, fs


@functools.lru_cache(maxsize=32)
def load_apnea_annotations(infant_id: str) -> Tuple[np.ndarray, float]:
    """
    Loads verified respiration pause annotations from the .resp file.
    Cached in memory for instantaneous sub-millisecond responses.
    """
    record_path = get_picsdb_path(infant_id, "resp")
    ann = wfdb.rdann(record_path, "resp")
    fs = float(ann.fs)
    samples = np.asarray(ann.sample, dtype=np.float64) / fs
    return samples, fs
