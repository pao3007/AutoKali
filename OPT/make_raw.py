def make_opt_raw(file_path, num_lines_to_skip):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Skip specified number of lines
    processed_lines = lines[num_lines_to_skip:]

    # Save the modified lines back to the file
    with open(file_path, 'w') as file:
        file.writelines(processed_lines)