def multiply_numbers(file_path, num_lines_to_skip):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Skip specified number of lines
    lines_to_process = lines[num_lines_to_skip:]

    # Multiply each number with -1
    processed_lines = []
    for line in lines_to_process:
        numbers = line.split()  # Split the line into individual numbers
        multiplied_numbers = [str(-1 * float(num)) for num in numbers]  # Multiply each number by -1
        processed_line = '\t'.join(multiplied_numbers) + '\n'  # Join the multiplied numbers with tabs
        processed_lines.append(processed_line)

    # Save the modified lines back to the file
    with open(file_path, 'w') as file:
        file.writelines(processed_lines)

# Example usage

# Example usage
file_path = r'C:\Users\lukac\Desktop\Sylex\TEST_DATA\REF\test\REF\meranie3.txt'  # Replace with your file path
num_lines_to_skip = 6  # Specify the number of lines to skip

multiply_numbers(file_path, num_lines_to_skip)