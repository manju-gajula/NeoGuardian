import wfdb

# Load Infant 1 ECG annotation file
record_path = "data/picsdb/infant1_ecg"

annotations = wfdb.rdann(record_path, "atr")

# Sampling frequency of the ECG
fs = 250

print("Bradycardia annotation file loaded!")
print("Total annotations:", len(annotations.sample))

print("\nFirst 10 bradycardia events:")
print("-" * 55)
print("Event\tSample\t\tTime (seconds)\tTime (minutes)")
print("-" * 55)

for i, sample in enumerate(annotations.sample[:10]):
    time_seconds = sample / fs
    time_minutes = time_seconds / 60

    print(
        f"{i + 1}\t{sample}\t\t"
        f"{time_seconds:.2f}\t\t"
        f"{time_minutes:.2f}"
    )