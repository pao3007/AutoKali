import os

import matplotlib.pyplot as plt
import numpy as np

destination_folder = "C:/Users/lukac/Desktop/Sylex/TEST_DATA/REF"
data_file = 'testData.txt'

file_path = os.path.join(destination_folder, data_file)

sample_rate = 1/1000

data = np.loadtxt(file_path)

time = np.arange(0, len(data) * sample_rate, sample_rate)

plt.plot(time, data)

plt.xlabel('Čas [s]')
plt.ylabel('Napätie [V]')
plt.title('Priebeh napätia')
plt.grid(True)

plt.show()
