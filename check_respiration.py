import wfdb
import matplotlib.pyplot as plt

# PICSDB Infant 1 respiration recording
record_path = "data/picsdb/infant1_resp"

# Load respiration signal
record = wfdb.rdrecord(record_path)

print("PICSDB respiration loaded successfully!")
print("Record name:", record.record_name)
print("Number of samples:", record.sig_len)
print("Sampling frequency:", record.fs)
print("Number of signals:", record.n_sig)
print("Signal names:", record.sig_name)

# -----------------------------------------
# Plot first 30 seconds
# -----------------------------------------

seconds = 30
samples = int(seconds * record.fs)

signal = record.p_signal[:samples, 0]

time = [
    i / record.fs
    for i in range(len(signal))
]

plt.figure(figsize=(14, 5))

plt.plot(time, signal)

plt.title("Infant 1 - Respiration Signal (First 30 Seconds)")
plt.xlabel("Time (seconds)")
plt.ylabel("Respiration amplitude")

plt.grid(True)

plt.show()