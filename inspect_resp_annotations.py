import wfdb
import numpy as np


# ==========================================
# SETTINGS
# ==========================================

RECORD_PATH = "data/picsdb/infant1_resp"


# ==========================================
# 1. LOAD RESPIRATION ANNOTATIONS
# ==========================================

print("Loading respiration annotations...")
annotations = wfdb.rdann(
    RECORD_PATH,
    "resp"
)

print("Annotations loaded successfully!")


# ==========================================
# 2. BASIC INFORMATION
# ==========================================

print("\n======================================")
print("RESPIRATION ANNOTATION INSPECTION")
print("======================================")

print(
    "Total annotations:",
    len(annotations.sample)
)

print(
    "Annotation sampling frequency:",
    annotations.fs
)


# ==========================================
# 3. COUNT ANNOTATION SYMBOLS
# ==========================================

symbols = np.array(annotations.symbol)

unique_symbols, counts = np.unique(
    symbols,
    return_counts=True
)

print("\nAnnotation symbol counts:")

for symbol, count in zip(
    unique_symbols,
    counts
):
    print(
        f"'{symbol}': {count}"
    )


# ==========================================
# 4. SHOW FIRST 50 ANNOTATIONS
# ==========================================

print("\nFirst 50 annotations:")

for i in range(
    min(50, len(annotations.sample))
):

    sample = annotations.sample[i]

    time_seconds = sample / annotations.fs

    symbol = annotations.symbol[i]

    print(
        f"{i + 1:3d}. "
        f"Sample: {sample:8d} | "
        f"Time: {time_seconds:10.2f} sec | "
        f"Symbol: '{symbol}'"
    )


# ==========================================
# 5. SHOW ANNOTATIONS FROM DIFFERENT
#    PARTS OF THE RECORD
# ==========================================

print("\n======================================")
print("ANNOTATIONS ACROSS THE RECORD")
print("======================================")


total_duration = (
    annotations.sample[-1]
    / annotations.fs
)

print(
    "Approximate annotation duration:",
    round(total_duration / 60, 2),
    "minutes"
)


check_times = [
    0,
    60,
    120,
    180,
    300,
    600,
    900
]


for target_time in check_times:

    target_sample = int(
        target_time * annotations.fs
    )

    distances = np.abs(
        annotations.sample - target_sample
    )

    closest_index = np.argmin(distances)

    closest_sample = (
        annotations.sample[closest_index]
    )

    closest_time = (
        closest_sample
        / annotations.fs
    )

    closest_symbol = (
        annotations.symbol[closest_index]
    )

    print(
        f"\nRequested: {target_time / 60:.2f} min"
    )

    print(
        f"Closest:   {closest_time / 60:.2f} min"
    )

    print(
        f"Sample:    {closest_sample}"
    )

    print(
        f"Symbol:    '{closest_symbol}'"
    )


print("\nInspection complete.")