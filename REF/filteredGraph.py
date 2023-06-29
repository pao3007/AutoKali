import os
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import numpy as np

destination_folder = "C:/Users/lukac/Desktop/Sylex/TEST_DATA/REF"
data_file = 'testData.txt'
file_path = os.path.join(destination_folder, data_file)
sample_rate = 1/1000

def savitzky_golay_filter(data, window_size, poly_order):
    filtered_data = savgol_filter(data, window_size, poly_order)
    return filtered_data

data = np.loadtxt(file_path)
filt_data = savitzky_golay_filter(data, 6, 4)

time = np.arange(0, len(data) * sample_rate, sample_rate)
filt_time = np.arange(0, len(filt_data) * sample_rate, sample_rate)

plt.figure()
plt.plot(time, data)
plt.xlabel('Čas [s]')
plt.ylabel('Napätie [V]')
plt.title('Priebeh napätia')
plt.grid(True)
plt.show(block=False)

plt.figure()
plt.plot(filt_time, filt_data)
plt.xlabel('Čas [s]')
plt.ylabel('Napätie [V]')
plt.title('Filtrovaný priebeh napätia')
plt.grid(True)

plt.show(block=False)

plt.show()




