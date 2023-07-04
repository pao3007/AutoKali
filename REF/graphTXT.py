import os
import matplotlib.pyplot as plt
import numpy as np
import yaml

data_file = '0407test.txt'

with open('a_ref_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

sample_rate = config['measurement']['sample_rate']
destination_folder = config['save_data']['destination_folder']

file_path = os.path.join(destination_folder, data_file)

sample_rate = 1/sample_rate

with open(file_path) as f:
    lines = (line for line in f if not line.startswith('#'))
    data = np.loadtxt(lines)

time = np.arange(0, len(data) * sample_rate, sample_rate)

plt.plot(time, data)

plt.xlabel('Čas [s]')
plt.ylabel('Napätie [V]')
plt.title('Priebeh napätia')
plt.grid(True)

plt.show()

