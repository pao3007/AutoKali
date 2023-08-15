import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft

# Load the data
samples = np.loadtxt(r"C:\Users\lukac\Documents\Sylex_sensors_export\optical_raw\test.csv")

# Let's assume sampling_rate is given (in Hz), adjust accordingly
sampling_rate = 800.0  # samples per second

# Calculate the time for each sample
timestamps = np.arange(len(samples)) / sampling_rate

# Perform Fast Fourier Transform
yf = fft(samples)
xf = np.linspace(0.0, 1.0/(2.0/sampling_rate), len(samples)//2)

# Check if the signal forms a periodic waveform
# If there is a peak in the frequency domain, we can say that there is a periodic signal
peak_threshold = 10  # adjust this threshold according to your needs
peak_freqs = xf[np.abs(yf[:len(samples)//2]) > peak_threshold]
if len(peak_freqs) > 0:
    print(f"Data seems to form a periodic waveform with dominant frequencies at: {peak_freqs} Hz")
else:
    print("Data doesn't seem to form a periodic waveform.")

# Plot the FFT result
plt.plot(xf, 2.0/len(samples) * np.abs(yf[:len(samples)//2]))
plt.grid()
plt.show()
