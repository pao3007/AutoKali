import numpy as np

sampling_rate = 800
# Generate sample data
file_path=r"C:\Users\lukac\Documents\Sylex_sensors_export\optical_raw\test.csv"
with open(file_path, 'r') as file:
    samples = file.read()

timestamps = np.arange(len(samples)) / sampling_rate

print(timestamps)


# Measure timestamps and samples
timestamp_samples = list(zip(timestamps, samples))

# Check if samples form a wave pattern
is_wave = False

if len(timestamp_samples) >= 3:
    timestamps, samples = zip(*timestamp_samples)
    timestamps = np.array(timestamps)
    samples = np.array(samples)

    # Calculate time intervals between samples
    time_intervals = np.diff(timestamps)

    # Check if time intervals are constant
    if np.allclose(time_intervals, time_intervals[0]):
        # Calculate differences between consecutive samples
        differences = np.diff(samples)

        # Check if differences alternate in sign
        if np.all(np.sign(differences[:-1]) != np.sign(differences[1:])):
            is_wave = True

if is_wave:
    print("The samples form a wave pattern.")
else:
    print("The samples do not form a wave pattern.")
