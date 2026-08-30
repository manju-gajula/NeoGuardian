import wfdb
import matplotlib.pyplot as plt

# Load Infant 1 ECG
record_path = "data/picsdb/infant1_ecg"
record = wfdb.rdrecord(record_path)

# Take the first 10 seconds
seconds = 10
samples = int(seconds * record.fs)

ecg = record.p_signal[:samples, 0]

# Create time axis
time = [i / record.fs for i in range(samples)]

# Plot ECG
plt.figure(figsize=(12, 4))
plt.plot(time, ecg)

plt.title("Infant 1 - ECG Signal (First 10 Seconds)")
plt.xlabel("Time (seconds)")
plt.ylabel("ECG Amplitude")
plt.grid(True)

plt.show()