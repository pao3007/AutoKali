import os
import csv


def save_statistics_to_csv(folder_path, file_name, date, serial_number, sensitivity, wl1, wl2=None):
    wavelengths = str(wl1)
    if wl2 is not None:
        wavelengths += "/" + str(wl2)

    # Append .csv to the file name
    file_name += ".csv"

    # Check if folder exists, if not, create it
    stats_folder_path = os.path.join(folder_path, "statistics")
    if not os.path.exists(stats_folder_path):
        os.makedirs(stats_folder_path)

    # Check if file exists, if not, create it and write header
    file_path = os.path.join(stats_folder_path, file_name)
    file_exists = os.path.exists(file_path)

    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(['Date', 'Serial Number', 'Wavelengths', 'Sensitivity'])

        writer.writerow([date, serial_number, wavelengths, str(sensitivity)])


date = "2023-09-13"
# Example usage
folder_path = r"C:\Users\PC\Desktop\Sylex\testDB"
file_name = r"C:\Users\PC\Desktop\Sylex\dsaad.yaml"  # No .csv extension needed here
serial_number = "SN12345"
wl1 = 999.1
wl2 = 899.1

sensitivity = 99.99

file_name_with_extension = os.path.basename(file_name)
file_name_without_extension = os.path.splitext(file_name_with_extension)[0]

save_statistics_to_csv(folder_path, file_name_without_extension, date, serial_number, sensitivity, wl1, wl2=wl2)
