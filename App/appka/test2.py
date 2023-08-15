import os

import pandas as pd
from matplotlib import pyplot as plt

os.chdir("C:/Users/lukac/Documents/Sylex_sensors_export/optical")
# Read the CSV file with the appropriate delimiter and skip initial non-relevant rows
df = pd.read_csv('m20230808_114555.csv', delimiter=';', skiprows=3)

# Extract the 3rd column values
ch_1_r_1_values = df[' CH_1_R_1'].tolist()
rounded_values = [round(val, 3) for val in ch_1_r_1_values]
sampling_time = 1/40
# Remove any leading or trailing whitespaces
# ch_1_r_1_values = [val.strip() for val in ch_1_r_1_values]
time_intervals = [i * sampling_time for i in range(len(ch_1_r_1_values))]
plt.plot(time_intervals, rounded_values, linestyle='-', color='b')

# Add title and labels to the plot
plt.title("Measured Data vs. Time")
plt.xlabel("Time (seconds)")
plt.ylabel("Measured Data")

# Display the plot
plt.grid(True)
plt.show()
