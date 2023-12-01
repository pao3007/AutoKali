import os
import re

def rename_files_in_folder(folder_path):
    # Extract the folder name
    folder_name = os.path.basename(folder_path)

    try:
        # List all files in the directory
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        for file in files:
            # Using regex to find the required pattern
            # This regex pattern expects files to start with a number sequence, followed by an underscore, another number sequence, and then optionally anything else until ".csv"
            match = re.search(r'(\d+)_(\d+)(.*)?\.csv', file)
            if match:
                prefix, number, _ = match.groups()  # We ignore the third group (suffix) for the new filename

                # Pad the number
                padded_number = number.zfill(4)

                # Construct new file name
                new_name = f"{prefix}_{padded_number}_{folder_name}.csv"

                # Path of the old and new files
                old_file = os.path.join(folder_path, file)
                new_file = os.path.join(folder_path, new_name)

                # Renaming the file
                os.rename(old_file, new_file)
                print(f"Renamed '{file}' to '{new_name}'")

    except Exception as e:
        print(f"Error occurred: {e}")

# Example usage
rename_files_in_folder(r"C:\Users\PC\Desktop\opt")
