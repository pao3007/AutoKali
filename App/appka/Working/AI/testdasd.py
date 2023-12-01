import re  # import regular expression module

def extract_sensitivity_from_csv(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            # Use regular expression to match the line containing 'Sensitivity'
            if re.search(r"# Sensitivity\s*:", line):
                # Get the next line that contains the sensitivity value
                sensitivity_line = lines[lines.index(line) + 1].strip()
                # Extract the numerical value using regex
                sensitivity_value = re.findall(r"[\d.]+", sensitivity_line)[0]
                return float(sensitivity_value)

# Replace 'your_file.csv' with the path to your .csv file
file_path = "./datasets/246630_0001_cal.csv"
sensitivity = extract_sensitivity_from_csv(file_path)
print(f"Sensitivity Value: {sensitivity}")
