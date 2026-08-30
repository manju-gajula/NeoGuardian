import wfdb
import numpy as np

record_path = "data/picsdb/infant1_resp"

# Load respiration annotations
annotations = wfdb.rdann(record_path, "resp")

print("======================================")
print("RESPIRATION ANNOTATIONS")
print("======================================")

print("Annotation file loaded successfully!")
print("Number of annotations:", len(annotations.sample))

print("\nFirst 30 annotation sample positions:")
print(annotations.sample[:30])

print("\nAnnotation symbols:")
print(annotations.symbol[:30])

# Convert sample positions to seconds
times = annotations.sample / annotations.fs

print("\nFirst 30 annotation times:")
for i in range(min(30, len(times))):
    print(
        f"{i + 1}. "
        f"Sample: {annotations.sample[i]} | "
        f"Time: {times[i]:.2f} seconds | "
        f"Symbol: {annotations.symbol[i]}"
    )

print("\nAnnotation frequency:")
print("Annotation sampling frequency:", annotations.fs)