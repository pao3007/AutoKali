import os
import time


def check_new_files(folder_path):
    # Get the initial set of files in the folder
    initial_files = set(os.listdir(folder_path))

    while True:
        # Sleep for some time
        time.sleep(1)

        # Get the current set of files in the folder
        current_files = set(os.listdir(folder_path))

        # Find the difference between the current and initial files
        new_files = current_files - initial_files

        if new_files:
            print("New file(s) created:")
            for file in new_files:
                print(file)

            # You can perform additional actions here, such as processing the new file(s)

        # Update the initial set of files
        initial_files = current_files


# Specify the path to the folder you want to monitor
folder_path = r"C:\Users\lukac\Documents\Sylex_sensors_export\optical"

check_new_files(folder_path)
