import subprocess
import os

class ThreadOptReadSamplesModBus(PyQt5.QtCore.QThread):
    command_line = "modpoll -t 3 -p 501 -l 1 -r 101 -c 10 127.0.0.1"

    def __init__(self, file_name, measure_time, channels, modpoll_directory):
        super().__init__()
        self.file_name = file_name
        self.measure_time = measure_time*1000
        self.channels = channels
        self.modpoll_directory = "C:/Users/lukac/Desktop/Sylex/modpoll-3.10/win"

    def run(self):
        # Open the output file:
        with open(self.file_name + ".csv", "w") as outfile:
            os.chdir(self.modpoll_directory)
            process = subprocess.Popen(self.command_line, stdout=outfile, shell=True)

            # Wait for a certain number of seconds:
            PyQt5.QtCore.QThread.msleep(self.measure_time)  # adjust this value as needed

            # Send the SIGINT signal to the process (this is the same as pressing Ctrl+C in the terminal):
            process.terminate()

            # Wait for the process to terminate:
            process.wait()
            outfile.close()
            samples = self.parse_modpoll_output()
            with open(self.file_name + ".csv", "w", newline='') as file:
                writer = csv.writer(file, delimiter=';')
                # Transpose the samples list to get rows instead of columns
                rows = zip_longest(*samples, fillvalue="")
                for row in rows:
                    writer.writerow(row)

    def parse_modpoll_output(self):
        with open(self.file_name + ".csv", "r") as file:
            lines = file.readlines()
            file.close()

        data = {}
        for line in lines:
            # Skip lines that do not contain ':' character:
            if ':' not in line:
                continue

            # Split the line into address and value:
            parts = line.split(':')
            if len(parts) != 2:
                continue

            address, value = parts
            try:
                address = int(address.strip('[] '))
                value = int(value.strip())
            except ValueError:
                continue

            # Store in the dictionary, if address is not in data initialize it with empty list
            if address not in data:
                data[address] = []

            # Append to the list for this address:
            data[address].append(value)

        # samples = []
        # index = 0
        # while index < len(data[101]):
        #     samples.append(data[101][index] + data[102][index]/10000)
        #     index += 1

        samples = [[] for _ in range(self.channels)]  # Create a list of empty lists, one for each channel

        for channel in range(self.channels):
            register_numbers = [101 + 100 * channel,
                                102 + 100 * channel]  # Calculate the register numbers for this channel

            index = 0
            while index < len(data[register_numbers[0]]):
                # Add samples from this channel's registers to the channel's sample list
                samples[channel].append(data[register_numbers[0]][index] + data[register_numbers[1]][index] / 10000)
                index += 1
        return samples



