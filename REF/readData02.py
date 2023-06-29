import nidaqmx
import os
from nidaqmx.constants import AcquisitionType
import datetime

i = 0
sample_rate = 100
number_of_samples_per_channel = 10000
destination_folder = "C:/Users/lukac/Desktop/Sylex/TEST_DATA/REF"

with nidaqmx.Task() as task:
    #nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai2", terminal_config=nidaqmx.constants.TerminalConfiguration.DEFAULT, min_val=-1.0, max_val=1.0)

    #časovanie resp. vzorkovacia freqvencia, pocet vzoriek
    task.timing.cfg_samp_clk_timing(sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)


    task.start()

    #data = task.read(number_of_samples_per_channel=number_of_samples_per_channel, timeout=nidaqmx.constants.WAIT_INFINITELY)

    #task.stop()

os.makedirs(destination_folder, exist_ok=True)

file_path = os.path.join(destination_folder, "testData.txt")

# Open the file in write mode and write the list elements

with open(file_path, 'w') as file:
        # Read and write the acquired data with timestamps
        while True:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            data = task.read(number_of_samples_per_channel=1)
            file.write(f"Timestamp: {timestamp} Data: {data[0]}\n")
            i = i + 1

            # Break the loop after a certain number of samples
            if i > 10000:
                break


task.stop()

print("Data written to file successfully.")
