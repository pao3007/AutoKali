import os

def create_folders():
    documents_path = os.path.expanduser('~/Documents')
    main_folder_name = 'Sylex_sensors_export'
    subfolder1_name = 'reference'
    subfolder2_name = 'optical'

    main_folder_path = os.path.join(documents_path, main_folder_name)
    subfolder1_path = os.path.join(main_folder_path, subfolder1_name)
    subfolder2_path = os.path.join(main_folder_path, subfolder2_name)

    # Check if the main folder already exists
    if not os.path.exists(main_folder_path):
        # Create the main folder
        os.makedirs(main_folder_path)
        print(f"Main folder created: {main_folder_path}")
    else:
        print(f"Main folder already exists: {main_folder_path}")

    # Create the subfolders inside the main folder
    os.makedirs(subfolder1_path, exist_ok=True)
    os.makedirs(subfolder2_path, exist_ok=True)
    print(f"Subfolder 1 created: {subfolder1_path}")
    print(f"Subfolder 2 created: {subfolder2_path}")

# Call the function to create the folders
create_folders()
