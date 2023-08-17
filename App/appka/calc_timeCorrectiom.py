import numpy as np
import os
import AC_functions_2FBG_v3 as fun

ref_sampling_rate = 12800  # Adjust according to the reference sensor's sampling rate
opt_sampling_rate = 800  # Adjust according to the optical sensor's sampling rate

# Fake data generation (replace with your real data)
ref_folder = r"C:\Users\lukac\Documents\Sylex_sensors_export\reference_raw"
opt_folder = r"C:\Users\lukac\Documents\Sylex_sensors_export\optical_raw"

file = "242358_05_autoCalib.csv"


# optical_sensor = fun.calculateAC()
def time_correction():
    def detect_max_in_first_second(data, sampling_rate):
        data_in_first_second = data[:int(sampling_rate)]
        return np.argmax(np.abs(data_in_first_second))

    ref_data_path = os.path.join(ref_folder, file)
    opt_data_path = os.path.join(opt_folder, file)

    reference_sensor = np.loadtxt(ref_data_path)
    DataOptRel = np.loadtxt(opt_data_path)

    optical_sensor = fun.calculateAC(
        -(DataOptRel[:, 0] - DataOptRel[:, 1]) + (round(np.mean(DataOptRel[100:200, 0]), 5) -
                                                  round(np.mean(DataOptRel[100:200, 1]), 5)),
        1.35)
    reference_sensor = reference_sensor/ 1.079511
    ref_max_idx = detect_max_in_first_second(reference_sensor, ref_sampling_rate)
    opt_max_idx = detect_max_in_first_second(optical_sensor, opt_sampling_rate)

    # Convert the index to time using the respective sampling rates
    ref_time = float(ref_max_idx) / float(ref_sampling_rate)
    opt_time = float(opt_max_idx) / float(opt_sampling_rate)

    return (opt_time - ref_time), optical_sensor, reference_sensor


time_Correction_data, optical_data, reference_data = time_correction()
print(time_Correction_data)

import numpy as np
import matplotlib.pyplot as plt


# Sample rates
reference_sampling_rate = ref_sampling_rate  # 1 kHz
optical_sampling_rate = opt_sampling_rate   # 2 kHz

# Calculate time arrays based on sampling rates
reference_time = np.linspace(0, len(reference_data)/reference_sampling_rate, len(reference_data))
reference_time = reference_time + time_Correction_data
optical_time = np.linspace(0, len(optical_data)/optical_sampling_rate, len(optical_data))

# Plot
plt.figure(figsize=(10,6))

plt.plot(reference_time, reference_data, label='Reference Data', linestyle='-')
plt.plot(optical_time, optical_data, label='Optical Data', linestyle='-')

plt.xlabel('Time (seconds)')
plt.ylabel('Amplitude')
plt.title('Reference and Optical Data')
plt.legend()
plt.grid(True)

plt.show()

