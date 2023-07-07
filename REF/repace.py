def replace_semicolon(file_path, num_lines_to_skip):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Skip specified number of lines
    lines_to_process = lines[num_lines_to_skip:]

    # Replace semicolon with tab character
    processed_lines = [line.replace(';', '\t') for line in lines_to_process]

    # Save the modified lines back to the file
    with open(file_path, 'w') as file:
        file.writelines(processed_lines)

# Example usage
file_path = r'C:\Users\lukac\Desktop\Sylex\TEST_DATA\REF\test\OPT\meranie3.txt'  # Replace with your file path
num_lines_to_skip = 4  # Specify the number of lines to skip

replace_semicolon(file_path, num_lines_to_skip)
