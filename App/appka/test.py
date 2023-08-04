import csv
from itertools import zip_longest

def write_samples_to_csv(file_name, samples):
    with open(file_name + ".csv", "w", newline='') as file:
        writer = csv.writer(file, delimiter=';')
        # Transpose the samples list to get rows instead of columns
        rows = zip_longest(*samples, fillvalue=" ")
        for row in rows:
            writer.writerow(row)

def extract_samples(data, channels):
    # This function expects data to be a dict-like object mapping register numbers to lists of samples.
    # The function returns a list of lists, where each inner list contains the samples for a single channel.

    samples = [[] for _ in range(channels)] # Create a list of empty lists, one for each channel

    for channel in range(channels):
        register_numbers = [101 + 100*channel, 102 + 100*channel] # Calculate the register numbers for this channel

        index = 0
        while index < len(data[register_numbers[0]]):
            # Add samples from this channel's registers to the channel's sample list
            samples[channel].append(data[register_numbers[0]][index] + data[register_numbers[1]][index]/10000)
            index += 1

    return samples


# Usage example:
data = {101: [1, 2, 3], 102: [4, 5, 6], 201: [7, 8, 9], 202: [10, 11, 12]}
channels = 2 # This will get channels 0 and 1
samples = extract_samples(data, channels)
write_samples_to_csv("test_csv", samples)
