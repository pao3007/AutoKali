import os
import matplotlib.pyplot as plt
import numpy as np
import yaml

data_file = 'Test_001.txt'

with open('a_ref_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

sample_rate = config['measurement']['sample_rate']
destination_folder = "C:/Users/lukac/Desktop/Sylex/TEST_DATA/REF/data_program"

file_path = os.path.join(destination_folder, data_file)

sample_rate = 1/sample_rate

with open(file_path, 'r') as file:
    third_columns = []
    for line in file:
        columns = line.split()
        if len(columns) >= 3:
            value = columns[2].replace(',', '.')
            third_columns.append(float(value))


data = np.array(third_columns, dtype=float)

print(data)


time = np.arange(0, len(data) * sample_rate, sample_rate)

plt.plot(time, data)

plt.xlabel('Čas [s]')
plt.ylabel('Napätie [V]')
plt.title('Priebeh napätia')
plt.grid(True)

plt.show()
