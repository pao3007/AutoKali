import nidaqmx
import os
import numpy as np
from nidaqmx.constants import AcquisitionType
import time
import matplotlib.pyplot as plt
import yaml

from datetime import datetime

#otovríme config file
with open('a_ref_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

#info o vzorkach
sample_rate = config['measurement']['sample_rate']
number_of_samples_per_channel = config['measurement']['number_of_samples_per_channel']

#nazov zariadenia a channel
deviceName_channel = config['device']['name'] + '/' + config['device']['channel']

#nazov txt suboru a poloha priecinku
ref_name = config['save_data']['ref_name']
destination_folder = config['save_data']['destination_folder']

def plot_data():
    sample_rate_sec = 1 / sample_rate

    time = np.arange(0, len(data) * sample_rate_sec, sample_rate_sec)

    plt.plot(time, data)

    plt.xlabel('Čas [s]')
    plt.ylabel('Napätie [V]')
    plt.title('Priebeh napätia')
    plt.grid(True)

    plt.show()

def save_data():
    from datetime import date
    today = date.today()
    date = today.strftime("%b-%d-%Y")
    os.makedirs(destination_folder, exist_ok=True)

    file_path = os.path.join(destination_folder, ref_name)

    with open(file_path, 'w') as file:
        file.write("# " + date + '\n')
        file.write("# " + time_string + '\n')
        file.write("# Dĺžka merania : " + str(round(elapsed_time/1000,2)) + "s" + '\n')
        file.write("# Vzorkovacia frekvencia : " + str(sample_rate) + '\n')
        file.write("# Počet vzoriek : " + str(number_of_samples_per_channel) + '\n')
        file.write("# Merane napätie :" + '\n')
        for item in data:
            file.write(str(item) + '\n')

    print("Zapisane do txt")

def start_measure():
    with nidaqmx.Task() as task:
        #nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        #task.ai_channels.add_ai_voltage_chan(deviceName_channel, terminal_config=nidaqmx.constants.TerminalConfiguration.DEFAULT, min_val=-1.0, max_val=1.0)

        task.ai_channels.add_ai_accel_chan(deviceName_channel, sensitivity=1.079511)
        #časovanie resp. vzorkovacia freqvencia, pocet vzoriek
        task.timing.cfg_samp_clk_timing(sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=number_of_samples_per_channel)

        print("Start merania")
        current_time = datetime.now().time()
        time_string = current_time.strftime("%H:%M:%S")
        start_time = time.time()
        #spustenie získavania vzoriek
        task.start()

        #čítam získane vzorky
        data = task.read(number_of_samples_per_channel=number_of_samples_per_channel, timeout=nidaqmx.constants.WAIT_INFINITELY)

        end_time = time.time()

        #stop
        task.stop()
        print("Stop merania")

        #dĺžka merania
        elapsed_time = (end_time - start_time) * 1000
        print(f"Cas trvania merania: {elapsed_time:.2f} ms")
    return data, elapsed_time, time_string

#zacatie merania
data, elapsed_time, time_string = start_measure()

#ulozenie dát do txt súboru
save_data()

#vytvorenie grafu
plot_data()



